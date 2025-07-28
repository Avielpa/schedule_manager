// app/AddAssignmentScreen.tsx
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
    // *** הוסר כאן הקוד שמוסיף את selectedDate באופן אוטומטי ***
    // if (selectedDate && typeof selectedDate === 'string' && !selectedDates.includes(selectedDate)) {
    //   setSelectedDates(prev => [...prev, selectedDate]);
    // }
  }, [soldierId, selectedDate, selectedDates]); // ה-dependency array נשאר כך כי הוא לא מזיק

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






















// // app/AddAssignmentScreen.tsx
// import React, { useState, useEffect } from 'react';
// import {
//   View,
//   Text,
//   TouchableOpacity,
//   StyleSheet,
//   ActivityIndicator,
//   Alert,
//   Switch,
//   Platform,
//   TextInput,
// } from 'react-native';
// import { useLocalSearchParams, router } from 'expo-router';
// import DateTimePicker from '@react-native-community/datetimepicker';
// import { soldierService } from '@/service/api'; // ייבא את soldierService

// export default function AddAssignmentScreen() {
//   const { soldierId, soldierName, schedulingRunId, selectedDate } = useLocalSearchParams();

//   const [constraintDate, setConstraintDate] = useState<Date>( // שיניתי את שם המשתנה ל-constraintDate
//     selectedDate ? new Date(selectedDate as string) : new Date()
//   );
//   const [showDatePicker, setShowDatePicker] = useState(false);
//   const [description, setDescription] = useState('אילוץ שהוגדר על ידי המשתמש'); // הוספת שדה תיאור
//   const [loading, setLoading] = useState(false);

//   useEffect(() => {
//     if (!soldierId) { // אין צורך ב-schedulingRunId עבור אילוץ
//       Alert.alert("שגיאה", "חסר soldierId");
//       router.back();
//     }
//   }, [soldierId]);

//   const handleAddConstraint = async () => { // שיניתי את שם הפונקציה ל-handleAddConstraint
//     setLoading(true);
//     try {
//       const payload = {
//         constraint_date: constraintDate.toISOString().split('T')[0], // פורמט תאריך YYYY-MM-DD
//         description: description, // שליחת התיאור
//       };

//       await soldierService.addSoldierConstraint(parseInt(soldierId as string), payload); // קריאה לפונקציה הנכונה

//       Alert.alert("הצלחה", `אילוץ נשמר עבור ${soldierName} בתאריך ${payload.constraint_date}`);
//       router.back();
//     } catch (error: any) {
//       console.error("שגיאה בהוספת אילוץ:", error); // הדפסת השגיאה לקונסול
//       const errorMessage = error?.message || "משהו השתבש"; // שגיאות מה-API מטופלות ב-handleResponse
//       Alert.alert("שגיאה", `נכשל להוסיף אילוץ: ${errorMessage}`);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const onChangeDate = (event: any, selected?: Date) => {
//     setShowDatePicker(Platform.OS === 'ios');
//     if (selected) setConstraintDate(selected); // עדכון constraintDate
//   };

//   return (
//     <View style={styles.container}>
//       <Text style={styles.title}>🚫 הוספת אילוץ</Text>
//       <Text style={styles.subtitle}>
//         לחייל: <Text style={styles.bold}>{soldierName}</Text>
//       </Text>

//       <View style={styles.field}>
//         <Text style={styles.label}>📅 תאריך אילוץ:</Text>
//         <TouchableOpacity
//           style={styles.datePickerButton}
//           onPress={() => setShowDatePicker(true)}
//         >
//           <Text style={styles.dateText}>{constraintDate.toLocaleDateString()}</Text>
//         </TouchableOpacity>
//       </View>

//       {showDatePicker && (
//         <DateTimePicker
//           value={constraintDate}
//           mode="date"
//           display="default"
//           onChange={onChangeDate}
//           minimumDate={new Date()}
//         />
//       )}

//       {/* אין צורך במתג "בבסיס/בבית" עבור אילוץ, זה רלוונטי לשיבוץ */}
//       {/* אם תרצה להוסיף שדה תיאור לאילוץ, תוכל לעשות זאת כך: */}
//       <View style={styles.field}>
//         <Text style={styles.label}>תיאור האילוץ (אופציונלי):</Text>
//         <TextInput
//           style={styles.textInput} // הוסף סגנון ל-TextInput
//           onChangeText={setDescription}
//           value={description}
//           placeholder="לדוגמה: חופשה, גימלים, קורס"
//         />
//       </View>


//       <TouchableOpacity style={styles.saveButton} onPress={handleAddConstraint}>
//         {loading ? (
//           <ActivityIndicator color="#fff" />
//         ) : (
//           <Text style={styles.saveText}>💾 שמור אילוץ</Text>
//         )}
//       </TouchableOpacity>

//       <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
//         <Text style={styles.cancelText}>ביטול</Text>
//       </TouchableOpacity>
//     </View>
//   );
// }

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     backgroundColor: '#fafafa',
//     paddingHorizontal: 24,
//     paddingTop: 60,
//   },
//   title: {
//     fontSize: 26,
//     fontWeight: 'bold',
//     color: '#333',
//     marginBottom: 10,
//   },
//   subtitle: {
//     fontSize: 16,
//     color: '#666',
//     marginBottom: 30,
//   },
//   bold: {
//     fontWeight: 'bold',
//     color: '#222',
//   },
//   field: {
//     marginBottom: 24,
//   },
//   label: {
//     fontSize: 16,
//     color: '#444',
//     marginBottom: 6,
//   },
//   datePickerButton: {
//     backgroundColor: '#e0e0e0',
//     padding: 12,
//     borderRadius: 8,
//     alignItems: 'center',
//   },
//   dateText: {
//     fontSize: 16,
//     color: '#222',
//   },
//   textInput: { // סגנון חדש עבור שדה הטקסט
//     borderWidth: 1,
//     borderColor: '#ccc',
//     borderRadius: 8,
//     padding: 10,
//     fontSize: 16,
//     backgroundColor: '#fff',
//   },
//   switchRow: {
//     flexDirection: 'row',
//     alignItems: 'center',
//   },
//   switchText: {
//     marginLeft: 12,
//     fontSize: 16,
//     color: '#222',
//   },
//   saveButton: {
//     backgroundColor: '#4caf50',
//     padding: 16,
//     borderRadius: 10,
//     alignItems: 'center',
//     marginTop: 10,
//   },
//   saveText: {
//     color: '#fff',
//     fontSize: 16,
//     fontWeight: 'bold',
//   },
//   cancelButton: {
//     padding: 14,
//     alignItems: 'center',
//     marginTop: 12,
//   },
//   cancelText: {
//     fontSize: 16,
//     color: '#d32f2f',
//   },
// });


































// // app/event/AddAssignmentScreen.tsx
// import React, { useState, useEffect } from 'react';
// import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, Switch } from 'react-native';
// import { router, useLocalSearchParams } from 'expo-router';
// import { addAssignment, soldierService } from '@/service/api'; // ודא ש-assignmentService מייצא את addAssignment

// export default function AddAssignmentScreen() {
//   const params = useLocalSearchParams();
//   const { soldierId, soldierName, schedulingRunId, selectedDate } = params;

//   const [isOnBase, setIsOnBase] = useState(false); // מצב האם החייל בבסיס או בבית
//   const [loading, setLoading] = useState(false);
//   const [assignmentDate, setAssignmentDate] = useState<string>(selectedDate as string || '');

//   useEffect(() => {
//     // ניתן להוסיף כאן לוגיקה נוספת אם תרצה, למשל, טעינת ערכי ברירת מחדל
//     if (!soldierId || !schedulingRunId) {
//       Alert.alert("שגיאה", "פרטי חייל או מזהה ריצת שיבוץ חסרים.");
//       router.back();
//     }
//   }, [soldierId, schedulingRunId]);

//   const handleAddAssignment = async () => {
//     if (!soldierId || !schedulingRunId || !assignmentDate) {
//       Alert.alert("שגיאה", "אנא מלא את כל השדות הנדרשים.");
//       return;
//     }

//     setLoading(true);
//     try {
//       await soldierService.addSoldierConstraint(soldierId, {
//           constraint_date: date,
//           description: "אילוץ מוגדר על ידי המשתמש",
//         })
//       Alert.alert("הצלחה", `שיבוץ נוסף בהצלחה ל${soldierName}`);
//       router.back(); // חזור למסך הקודם
//     } catch (error:any) {
//       console.error("שגיאה בהוספת שיבוץ:", error);
//       Alert.alert("שגיאה", `נכשל להוסיף שיבוץ: ${error.message || 'נסה שוב.'}`);
//     } finally {
//       setLoading(false);
//     }
//   };

//   if (loading) {
//     return <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />;
//   }

//   return (
//     <View style={styles.container}>
//       <Text style={styles.title}>הוספת שיבוץ חדש</Text>
//       <Text style={styles.subtitle}>עבור: {soldierName}</Text>

//       <View style={styles.inputGroup}>
//         <Text style={styles.label}>תאריך שיבוץ:</Text>
//         <TextInput
//           style={styles.input}
//           value={assignmentDate}
//           onChangeText={setAssignmentDate}
//           placeholder="YYYY-MM-DD"
//           keyboardType="numeric" // כדי להקל על הקלדת תאריכים
//         />
//         <Text style={styles.helpText}>פורמט: שנה-חודש-יום (לדוגמה: 2025-07-20)</Text>
//       </View>

//       <View style={styles.switchContainer}>
//         <Text style={styles.label}>האם החייל בבסיס?</Text>
//         <Switch
//           onValueChange={setIsOnBase}
//           value={isOnBase}
//           trackColor={{ false: "#767577", true: "#81b0ff" }}
//           thumbColor={isOnBase ? "#f5dd4b" : "#f4f3f4"}
//         />
//         <Text style={styles.switchText}>{isOnBase ? "בבסיס" : "בבית"}</Text>
//       </View>

//       <TouchableOpacity
//         style={styles.button}
//         onPress={handleAddAssignment}
//         disabled={loading}
//       >
//         <Text style={styles.buttonText}>הוסף שיבוץ</Text>
//       </TouchableOpacity>

//       <TouchableOpacity
//         style={[styles.button, styles.cancelButton]}
//         onPress={() => router.back()}
//       >
//         <Text style={styles.buttonText}>ביטול</Text>
//       </TouchableOpacity>
//     </View>
//   );
// }

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     padding: 20,
//     backgroundColor: '#f8f8f8',
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   loading: {
//     flex: 1,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   title: {
//     fontSize: 26,
//     fontWeight: 'bold',
//     marginBottom: 10,
//     color: '#3f51b5',
//   },
//   subtitle: {
//     fontSize: 18,
//     color: '#555',
//     marginBottom: 30,
//   },
//   inputGroup: {
//     width: '90%',
//     marginBottom: 20,
//   },
//   label: {
//     fontSize: 16,
//     marginBottom: 8,
//     color: '#444',
//     fontWeight: '600',
//   },
//   input: {
//     borderWidth: 1,
//     borderColor: '#ccc',
//     borderRadius: 8,
//     padding: 12,
//     fontSize: 16,
//     backgroundColor: '#fff',
//   },
//   helpText: {
//     fontSize: 12,
//     color: '#888',
//     marginTop: 5,
//     textAlign: 'left',
//   },
//   switchContainer: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     justifyContent: 'center',
//     marginBottom: 30,
//     backgroundColor: '#e3f2fd',
//     padding: 15,
//     borderRadius: 10,
//     width: '90%',
//     shadowColor: "#000",
//     shadowOffset: { width: 0, height: 1 },
//     shadowOpacity: 0.1,
//     shadowRadius: 2,
//     elevation: 2,
//   },
//   switchText: {
//     fontSize: 16,
//     marginLeft: 10,
//     color: '#444',
//   },
//   button: {
//     backgroundColor: '#6200ee',
//     padding: 15,
//     borderRadius: 10,
//     width: '90%',
//     alignItems: 'center',
//     marginVertical: 10,
//     shadowColor: "#000",
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.2,
//     shadowRadius: 3,
//     elevation: 3,
//   },
//   buttonText: {
//     color: 'white',
//     fontSize: 18,
//     fontWeight: 'bold',
//   },
//   cancelButton: {
//     backgroundColor: '#d32f2f',
//   },
// });