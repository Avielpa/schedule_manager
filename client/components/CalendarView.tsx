import React, { useState, useMemo } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { 
  format, 
  startOfMonth, 
  endOfMonth, 
  startOfWeek, 
  endOfWeek, 
  addDays, 
  addMonths,
  subMonths,
  isSameDay,
  isSameMonth,
  parseISO,
  eachDayOfInterval
} from "date-fns";
import { he } from "date-fns/locale";

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
    startOfMonth(parseISO(startDate))
  );

  const eventDates = useMemo(() => {
    const start = parseISO(startDate);
    const end = parseISO(endDate);
    
    return eachDayOfInterval({ start, end }).map(date => 
      format(date, "yyyy-MM-dd")
    );
  }, [startDate, endDate]);

  const daysInMonth = useMemo(() => {
    const start = startOfWeek(startOfMonth(currentMonth));
    const end = endOfWeek(endOfMonth(currentMonth));
    
    return eachDayOfInterval({ start, end });
  }, [currentMonth]);

  const handleSelect = (date: Date) => {
    const dateString = format(date, "yyyy-MM-dd");
    if (eventDates.includes(dateString)) {
      onDateSelect(dateString);
    }
  };

  const weekdaysShort = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ש'];

  return (
    <View style={styles.calendarContainer}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => setCurrentMonth(prev => subMonths(prev, 1))}>
          <Text style={styles.navButton}>{"<"}</Text>
        </TouchableOpacity>
        <Text style={styles.monthLabel}>{format(currentMonth, "MMMM yyyy", { locale: he })}</Text>
        <TouchableOpacity onPress={() => setCurrentMonth(prev => addMonths(prev, 1))}>
          <Text style={styles.navButton}>{">"}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.weekdays}>
        {weekdaysShort.map(day => (
          <Text key={day} style={styles.weekdayText}>{day}</Text>
        ))}
      </View>

      <View style={styles.daysContainer}>
        {daysInMonth.map((day) => {
          const dateStr = format(day, "yyyy-MM-dd");
          const isSelected = selectedDate === dateStr;
          const isInMonth = isSameMonth(day, currentMonth);
          const isToday = isSameDay(day, new Date());
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
                {format(day, "d")}
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
