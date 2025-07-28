import {
  soldierService, // ייבוא שירותי חיילים
  getSchedulingRunById, // ייבוא עבור פרטי הרצת השיבוץ
} from "@/service/api"; // נתיב מעודכן
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  TextInput,
  Alert,
  ScrollView,
} from "react-native";
// אין צורך לייבא Event אם אנחנו עובדים עם SchedulingRun
// import { Event } from "@/types/entities";
import DateTimePicker from "@react-native-community/datetimepicker";
import AntDesign from "@expo/vector-icons/AntDesign";
import { format } from "date-fns";

interface SchedulingRun {
  id: number;
  run_date: string;
  start_date: string;
  end_date: string;
  // Add any other properties that your backend returns for a scheduling run
}

interface Soldier {
  id: number;
  name: string;
  // Add other properties if your API returns them, e.g.:
  // is_on_base?: boolean;
  // constraints?: any[];
}

export default function AddSoldier() {
  const { id } = useLocalSearchParams();
  const schedulingRunId = Number(id); // שינוי ל-schedulingRunId
  const [schedulingRun, setSchedulingRun] = useState<SchedulingRun | null>(null); // שינוי ל-schedulingRun
  const [loading, setLoading] = useState(true);
  const [soldierName, setSoldierName] = useState("");
  const [isServingInBase, setIsServingInBase] = useState(true); // זהו פרמטר גלובלי של חייל, לא אילוץ
  const [constraintDates, setConstraintDates] = useState<string[]>([]);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [currentDateForPicker, setCurrentDateForPicker] = useState(new Date());

  useEffect(() => {
    // שלוף פרטי הרצת השיבוץ אם נדרש, למשל להצגת שם הרצת השיבוץ בכותרת
    const fetchSchedulingRun = async () => {
      try {
        const sr = await getSchedulingRunById(schedulingRunId);
        setSchedulingRun(sr as SchedulingRun);
      } catch (e) {
        console.error("שגיאה בשליפת פרטי הרצת שיבוץ:", e);
        Alert.alert("שגיאה", "לא ניתן לטעון את פרטי הרצת השיבוץ.");
      } finally {
        setLoading(false);
      }
    };

    if (schedulingRunId && !isNaN(schedulingRunId)) fetchSchedulingRun();
    else setLoading(false);
  }, [schedulingRunId]);

  const handleDateSelect = (event: any, selectedDate?: Date) => {
    setShowDatePicker(false);
    if (!selectedDate) return;

    // ולידציה שתאריך האילוץ הוא בתוך טווח התאריכים של השיבוץ
    if (schedulingRun) {
      const runStartDate = new Date(schedulingRun.start_date);
      const runEndDate = new Date(schedulingRun.end_date);
      if (selectedDate < runStartDate || selectedDate > runEndDate) {
        Alert.alert("תאריך לא חוקי", "תאריך האילוץ חייב להיות בתוך טווח תאריכי השיבוץ.");
        return;
      }
    }

    const dateString = format(selectedDate, "yyyy-MM-dd"); // שימוש ב-date-fns לפורמט אחיד
    if (constraintDates.includes(dateString)) {
      Alert.alert("תאריך כפול", "התאריך כבר קיים ברשימת האילוצים.");
    } else {
      setConstraintDates([...constraintDates, dateString].sort()); // מיון תאריכים
    }
  };

  const removeDate = (date: string) => {
    setConstraintDates((prev) => prev.filter((d) => d !== date));
  };

  const handleSubmit = async () => {
    if (!soldierName.trim()) {
      Alert.alert("שגיאה", "אנא הזן שם חייל.");
      return;
    }

    try {
      // 1. הוספת החייל למערכת
      // Explicitly cast the result to Soldier type if apiService isn't TypeScript
      const newSoldier: Soldier = await soldierService.addSoldier({
        name: soldierName.trim(),
      }) as Soldier; // Add 'as Soldier' here if apiService is JS, otherwise remove

      // 2. הוספת אילוצים לחייל החדש
      for (const date of constraintDates) {
        await soldierService.addSoldierConstraint(newSoldier.id, {
          constraint_date: date,
          description: "אילוץ מוגדר על ידי המשתמש",
        });
      }

      Alert.alert("הצלחה", "החייל והאילוצים נוספו בהצלחה!");
      router.back();
    } catch (error) {
      console.error("שגיאה בהוספת חייל:", error);
      Alert.alert("שגיאה", "אירעה שגיאה בהוספת החייל. אנא ודא שהשם ייחודי.");
    }
  };

  if (loading) {
    return <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />;
  }

  // שים לב: `event.name` הוחלף ל-`schedulingRun.id` או כל שדה מתאים אחר
  // אם אתה רוצה שם לקומפוננטת השיבוץ, וודא שיש שדה כזה במודל SchedulingRun.
  // כרגע המודל לא כולל שדה 'name' ישיר להרצת שיבוץ.
  const titleText = schedulingRun ? `הוספת חייל לשיבוץ: ${schedulingRun.id}` : "הוספת חייל";

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>{titleText}</Text>

      <Text style={styles.label}>שם החייל:</Text>
      <TextInput
        style={styles.input}
        placeholder="הזן שם חייל"
        value={soldierName}
        onChangeText={setSoldierName}
      />


      <Text style={styles.label}>אילוצים (תאריכים בהם החייל לא יכול להיות בבסיס):</Text>
      <TouchableOpacity style={styles.addDateButton} onPress={() => setShowDatePicker(true)}>
        <Text style={styles.addDateButtonText}>הוסף תאריך</Text>
      </TouchableOpacity>

      {showDatePicker && (
        <DateTimePicker
          value={currentDateForPicker}
          mode="date"
          display="default"
          onChange={handleDateSelect}
          minimumDate={schedulingRun ? new Date(schedulingRun.start_date) : undefined}
          maximumDate={schedulingRun ? new Date(schedulingRun.end_date) : undefined}
        />
      )}

      {constraintDates.length > 0 && (
        <View style={styles.constraintList}>
          {constraintDates.map((date) => (
            <View key={date} style={styles.constraintItem}>
              <Text style={styles.constraintDate}>{date}</Text>
              <TouchableOpacity onPress={() => removeDate(date)}>
                <AntDesign name="closecircle" size={20} color="red" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}

      <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
        <Text style={styles.submitButtonText}>שמור חייל</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#fff" },
  loading: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#6200ee",
    textAlign: "center",
    marginBottom: 20,
  },
  label: { fontSize: 16, fontWeight: "bold", marginBottom: 5, marginTop: 15 },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
  },
  radioGroup: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginVertical: 10,
  },
  radioButton: {
    padding: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#ddd",
    flex: 1,
    alignItems: "center",
    marginHorizontal: 5,
  },
  radioButtonSelected: {
    backgroundColor: "#6200ee",
    borderColor: "#6200ee",
  },
  radioText: { fontSize: 16, color: "#333" },
  radioTextSelected: { color: "#fff", fontWeight: "bold" },
  addDateButton: {
    backgroundColor: "#2196F3",
    padding: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 5,
  },
  addDateButtonText: { color: "#fff", fontSize: 16, fontWeight: "bold" },
  constraintList: {
    marginTop: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: "#eee",
    borderRadius: 8,
  },
  constraintItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderColor: "#eee",
    alignItems: "center",
  },
  constraintDate: { fontSize: 15, color: "#333" },
  submitButton: {
    backgroundColor: "#4CAF50",
    padding: 14,
    borderRadius: 10,
    marginTop: 25,
  },
  submitButtonText: { color: "#fff", fontSize: 18, fontWeight: "bold" },
  errorText: {
    fontSize: 18,
    textAlign: "center",
    color: "red",
    marginTop: 20,
  },
});




















// import { addSoldierToEvent, getEventById } from "@/service/api";
// import { router, useLocalSearchParams } from "expo-router";
// import React, { useEffect, useState } from "react";
// import {
//   Text,
//   View,
//   TouchableOpacity,
//   ActivityIndicator,
//   StyleSheet,
//   TextInput,
//   Alert,
//   ScrollView,
// } from "react-native";
// import { Event } from "@/types/entities";
// import DateTimePicker from "@react-native-community/datetimepicker";
// import AntDesign from "@expo/vector-icons/AntDesign";

// export default function AddSoldier() {
//   const { id } = useLocalSearchParams();
//   const eventId = Number(id);
//   const [event, setEvent] = useState<Event | null>(null);
//   const [loading, setLoading] = useState(true);
//   const [soldierName, setSoldierName] = useState("");
//   const [isServingInBase, setIsServingInBase] = useState(true);
//   const [constraintDates, setConstraintDates] = useState<string[]>([]);
//   const [showDatePicker, setShowDatePicker] = useState(false);
//   const [currentDateForPicker, setCurrentDateForPicker] = useState(new Date());

//   useEffect(() => {
//     const fetchEvent = async () => {
//       try {
//         const ev = await getEventById(eventId);
//         setEvent(ev);
//       } catch (e) {
//         console.error("Error fetching event:", e);
//         Alert.alert("שגיאה", "לא ניתן לטעון את פרטי האירוע.");
//       } finally {
//         setLoading(false);
//       }
//     };

//     if (eventId && !isNaN(eventId)) fetchEvent();
//     else setLoading(false);
//   }, [eventId]);

//   const handleDateSelect = (event: any, selectedDate?: Date) => {
//     setShowDatePicker(false);
//     if (!selectedDate) return;
//     const dateString = selectedDate.toISOString().split("T")[0];
//     if (constraintDates.includes(dateString)) {
//       Alert.alert("תאריך כפול", "התאריך כבר קיים ברשימת האילוצים.");
//     } else {
//       setConstraintDates([...constraintDates, dateString]);
//     }
//   };

//   const removeDate = (date: string) => {
//     setConstraintDates((prev) => prev.filter((d) => d !== date));
//   };

//   const handleSubmit = async () => {
//     if (!soldierName.trim()) {
//       Alert.alert("שגיאה", "אנא הזן שם חייל.");
//       return;
//     }

//     try {
//       await addSoldierToEvent(eventId, soldierName.trim(), isServingInBase, constraintDates);
//       Alert.alert("הצלחה", "החייל נוסף בהצלחה!");
//       router.back();
//     } catch (error) {
//       console.error("Error adding soldier:", error);
//       Alert.alert("שגיאה", "אירעה שגיאה בהוספת החייל.");
//     }
//   };

//   if (loading) {
//     return <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />;
//   }

//   if (!event) {
//     return (
//       <View style={styles.container}>
//         <Text style={styles.errorText}>אירוע לא נמצא</Text>
//       </View>
//     );
//   }

//   return (
//     <ScrollView style={styles.container}>
//       <Text style={styles.title}>הוספת חייל לאירוע: {event.name}</Text>

//       <Text style={styles.label}>שם החייל:</Text>
//       <TextInput
//         style={styles.input}
//         placeholder="הזן שם חייל"
//         value={soldierName}
//         onChangeText={setSoldierName}
//       />

//       <Text style={styles.label}>סוג שירות:</Text>
//       <View style={styles.radioGroup}>
//         <TouchableOpacity
//           style={[styles.radioButton, isServingInBase && styles.radioButtonSelected]}
//           onPress={() => setIsServingInBase(true)}
//         >
//           <Text style={[styles.radioText, isServingInBase && styles.radioTextSelected]}>
//             בבסיס
//           </Text>
//         </TouchableOpacity>
//         <TouchableOpacity
//           style={[styles.radioButton, !isServingInBase && styles.radioButtonSelected]}
//           onPress={() => setIsServingInBase(false)}
//         >
//           <Text style={[styles.radioText, !isServingInBase && styles.radioTextSelected]}>
//             בבית
//           </Text>
//         </TouchableOpacity>
//       </View>

//       <Text style={styles.label}>אילוצים (תאריכים בהם החייל לא יכול להיות בבסיס):</Text>
//       <TouchableOpacity style={styles.addDateButton} onPress={() => setShowDatePicker(true)}>
//         <Text style={styles.addDateButtonText}>הוסף תאריך</Text>
//       </TouchableOpacity>

//       {showDatePicker && (
//         <DateTimePicker
//           value={currentDateForPicker}
//           mode="date"
//           display="default"
//           onChange={handleDateSelect}
//         />
//       )}

//       {constraintDates.length > 0 && (
//         <View style={styles.constraintList}>
//           {constraintDates.map((date) => (
//             <View key={date} style={styles.constraintItem}>
//               <Text style={styles.constraintDate}>{date}</Text>
//               <TouchableOpacity onPress={() => removeDate(date)}>
//                 <AntDesign name="closecircle" size={20} color="red" />
//               </TouchableOpacity>
//             </View>
//           ))}
//         </View>
//       )}

//       <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
//         <Text style={styles.submitButtonText}>שמור חייל</Text>
//       </TouchableOpacity>
//     </ScrollView>
//   );
// }

// const styles = StyleSheet.create({
//   container: { flex: 1, padding: 20, backgroundColor: "#fff" },
//   loading: { flex: 1, justifyContent: "center", alignItems: "center" },
//   title: {
//     fontSize: 20,
//     fontWeight: "bold",
//     color: "#6200ee",
//     textAlign: "center",
//     marginBottom: 20,
//   },
//   label: { fontSize: 16, fontWeight: "bold", marginBottom: 5, marginTop: 15 },
//   input: {
//     borderWidth: 1,
//     borderColor: "#ccc",
//     padding: 10,
//     borderRadius: 8,
//     marginBottom: 10,
//   },
//   radioGroup: {
//     flexDirection: "row",
//     justifyContent: "space-around",
//     marginVertical: 10,
//   },
//   radioButton: {
//     padding: 10,
//     borderRadius: 6,
//     borderWidth: 1,
//     borderColor: "#ddd",
//     flex: 1,
//     alignItems: "center",
//     marginHorizontal: 5,
//   },
//   radioButtonSelected: {
//     backgroundColor: "#6200ee",
//     borderColor: "#6200ee",
//   },
//   radioText: { fontSize: 16, color: "#333" },
//   radioTextSelected: { color: "#fff", fontWeight: "bold" },
//   addDateButton: {
//     backgroundColor: "#2196F3",
//     padding: 12,
//     borderRadius: 6,
//     alignItems: "center",
//     marginTop: 5,
//   },
//   addDateButtonText: { color: "#fff", fontSize: 16, fontWeight: "bold" },
//   constraintList: {
//     marginTop: 10,
//     padding: 10,
//     borderWidth: 1,
//     borderColor: "#eee",
//     borderRadius: 8,
//   },
//   constraintItem: {
//     flexDirection: "row",
//     justifyContent: "space-between",
//     paddingVertical: 6,
//     borderBottomWidth: 1,
//     borderColor: "#eee",
//     alignItems: "center",
//   },
//   constraintDate: { fontSize: 15, color: "#333" },
//   submitButton: {
//     backgroundColor: "#4CAF50",
//     padding: 14,
//     borderRadius: 10,
//     marginTop: 25,
//     alignItems: "center",
//   },
//   submitButtonText: { color: "#fff", fontSize: 18, fontWeight: "bold" },
//   errorText: {
//     fontSize: 18,
//     textAlign: "center",
//     color: "red",
//     marginTop: 20,
//   },
// });
