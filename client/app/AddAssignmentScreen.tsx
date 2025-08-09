import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  TextInput,
  ScrollView,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { soldierService } from '@/service/api';
import { Calendar, DateData } from 'react-native-calendars'; 

interface MarkedDates {
  [date: string]: {
    selected: boolean;
    selectedColor: string;
    selectedTextColor: string;
  };
}

export default function AddAssignmentScreen() {
  const { soldierId, soldierName, schedulingRunId, selectedDate } = useLocalSearchParams();

  const [selectedDates, setSelectedDates] = useState<string[]>([]);
  const [description, setDescription] = useState('אילוץ שהוגדר על ידי המשתמש');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!soldierId) {
      Alert.alert("שגיאה", "חסר soldierId");
      router.back();
    }
  }, [soldierId]);

  const onDayPress = useCallback((day: DateData) => {
    const dateStr = day.dateString;

    if (selectedDates.includes(dateStr)) {
      setSelectedDates(prev => prev.filter(date => date !== dateStr));
    } else {
      setSelectedDates(prev => [...prev, dateStr]);
    }
  }, [selectedDates]);

  const markedDates: MarkedDates = selectedDates.reduce((acc: MarkedDates, date) => {
    acc[date] = { selected: true, selectedColor: '#6200ee', selectedTextColor: '#ffffff' };
    return acc;
  }, {});

  const handleAddConstraint = async () => {
    if (selectedDates.length === 0) {
      Alert.alert("שגיאה", "אנא בחר לפחות תאריך אחד לאילוץ.");
      return;
    }

    setLoading(true);
    try {
      for (const date of selectedDates) {
        const payload = {
          constraint_date: date,
          description: description,
        };
        await soldierService.addSoldierConstraint(parseInt(soldierId as string), payload);
      }

      Alert.alert("הצלחה", `אילוצים נשמרו עבור ${soldierName} ב-${selectedDates.length} תאריכים.`);
      router.back();
    } catch (error: any) {
      console.error("שגיאה בהוספת אילוץ:", error);
      const errorMessage = error?.message || "משהו השתבש";
      Alert.alert("שגיאה", `נכשל להוסיף אילוץ: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🚫 הוספת אילוץ</Text>
      <Text style={styles.subtitle}>
        לחייל: <Text style={styles.bold}>{soldierName}</Text>
      </Text>

      <View style={styles.field}>
        <Text style={styles.label}>📅 בחר תאריכי אילוץ:</Text>
        <Calendar
          onDayPress={onDayPress}
          markedDates={markedDates}
          minDate={new Date().toISOString().split('T')[0]}
          style={styles.calendar}
          theme={{
            selectedDayBackgroundColor: '#6200ee',
            selectedDayTextColor: '#ffffff',
            todayTextColor: '#6200ee',
            arrowColor: '#6200ee',
          }}
        />
        <Text style={styles.selectedDatesText}>
          נבחרו: {selectedDates.length} תאריכים ({selectedDates.sort().join(', ') || 'אין תאריכים נבחרים'})
        </Text>
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>תיאור האילוץ (אופציונלי):</Text>
        <TextInput
          style={styles.textInput}
          onChangeText={setDescription}
          value={description}
          placeholder="לדוגמה: חופשה, גימלים, קורס"
          multiline={true}
          numberOfLines={3}
        />
      </View>

      <TouchableOpacity style={styles.saveButton} onPress={handleAddConstraint}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.saveText}>💾 שמור אילוצים</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
        <Text style={styles.cancelText}>ביטול</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fafafa',
    paddingHorizontal: 24,
    paddingTop: 60,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
  },
  bold: {
    fontWeight: 'bold',
    color: '#222',
  },
  field: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    color: '#444',
    marginBottom: 6,
  },
  calendar: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 10,
    marginBottom: 10,
  },
  selectedDatesText: {
    fontSize: 14,
    color: '#555',
    textAlign: 'center',
    marginBottom: 10,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    backgroundColor: '#fff',
    minHeight: 80,
    textAlignVertical: 'top',
  },
  saveButton: {
    backgroundColor: '#4caf50',
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  saveText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  cancelButton: {
    padding: 14,
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 30,
  },
  cancelText: {
    fontSize: 16,
    color: '#d32f2f',
  },
});