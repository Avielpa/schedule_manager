import React, { useState, useMemo } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import moment from "moment";
import "moment/locale/he";

moment.locale("he");

interface CalendarViewProps {
  startDate: string;
  endDate: string;
  selectedDate: string | null;
  onDateSelect: (date: string) => void;
}

export default function CalendarView({
  startDate,
  endDate,
  selectedDate,
  onDateSelect,
}: CalendarViewProps) {
  const [currentMonth, setCurrentMonth] = useState(
    moment(startDate).startOf("month")
  );

  const eventDates = useMemo(() => {
    const dates: string[] = [];
    let current = moment(startDate);
    const end = moment(endDate);
    while (current.isSameOrBefore(end)) {
      dates.push(current.format("YYYY-MM-DD"));
      current.add(1, "day");
    }
    return dates;
  }, [startDate, endDate]);

  const daysInMonth = useMemo(() => {
    const start = moment(currentMonth).startOf("week");
    const end = moment(currentMonth).endOf("month").endOf("week");
    const days: moment.Moment[] = [];

    let day = start.clone();
    while (day.isSameOrBefore(end)) {
      days.push(day.clone());
      day.add(1, "day");
    }

    return days;
  }, [currentMonth]);

  const handleSelect = (date: moment.Moment) => {
    const dateString = date.format("YYYY-MM-DD");
    if (eventDates.includes(dateString)) {
      onDateSelect(dateString);
    }
  };

  return (
    <View style={styles.calendarContainer}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => setCurrentMonth(prev => prev.clone().subtract(1, "month"))}>
          <Text style={styles.navButton}>{"<"}</Text>
        </TouchableOpacity>
        <Text style={styles.monthLabel}>{currentMonth.format("MMMM YYYY")}</Text>
        <TouchableOpacity onPress={() => setCurrentMonth(prev => prev.clone().add(1, "month"))}>
          <Text style={styles.navButton}>{">"}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.weekdays}>
        {moment.weekdaysShort(true).map(day => (
          <Text key={day} style={styles.weekdayText}>{day}</Text>
        ))}
      </View>

      <View style={styles.daysContainer}>
        {daysInMonth.map((day) => {
          const dateStr = day.format("YYYY-MM-DD");
          const isSelected = selectedDate === dateStr;
          const isInMonth = day.month() === currentMonth.month();
          const isToday = day.isSame(moment(), "day");
          const isValid = eventDates.includes(dateStr);

          return (
            <TouchableOpacity
              key={dateStr}
              disabled={!isValid}
              onPress={() => handleSelect(day)}
              style={[
                styles.day,
                isSelected && styles.selectedDay,
                !isInMonth && styles.outsideMonth,
                isToday && styles.today,
                !isValid && styles.disabledDay
              ]}
            >
              <Text
                style={[
                  styles.dayText,
                  isSelected && styles.selectedDayText,
                  !isValid && styles.disabledDayText
                ]}
              >
                {day.date()}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  calendarContainer: {
    backgroundColor: "#f0f0f0",
    borderRadius: 10,
    padding: 15,
    marginVertical: 10,
    elevation: 2,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  navButton: {
    fontSize: 24,
    color: "#6200ee",
    fontWeight: "bold",
  },
  monthLabel: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#333",
  },
  weekdays: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 5,
  },
  weekdayText: {
    fontSize: 14,
    fontWeight: "bold",
    color: "#555",
    width: "14%",
    textAlign: "center",
  },
  daysContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-around",
  },
  day: {
    width: "13%",
    aspectRatio: 1,
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 6,
    marginVertical: 4,
  },
  dayText: {
    fontSize: 16,
    color: "#333",
  },
  selectedDay: {
    backgroundColor: "#6200ee",
  },
  selectedDayText: {
    color: "#fff",
    fontWeight: "bold",
  },
  today: {
    borderWidth: 2,
    borderColor: "#ff9800",
  },
  outsideMonth: {
    opacity: 0.4,
  },
  disabledDay: {
    backgroundColor: "#dcdcdc",
    opacity: 0.4,
  },
  disabledDayText: {
    color: "#888",
  },
});
