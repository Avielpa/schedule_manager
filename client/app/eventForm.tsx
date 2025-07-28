import AntDesign from "@expo/vector-icons/AntDesign";
import { useState } from "react";
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  TextInput,
  Alert,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { schedulingService } from "@/service/api"; // וודא ש-schedulingService קיים ומכיל את runNewScheduling

export default function SchedulingRunForm() {
  const router = useRouter();

  // שינוי שמות המשתנים כך שיתאימו לשדות של SchedulingRun
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [defaultBaseDaysTarget, setDefaultBaseDaysTarget] = useState("");
  const [defaultHomeDaysTarget, setDefaultHomeDaysTarget] = useState("");
  const [maxConsecutiveBaseDays, setMaxConsecutiveBaseDays] = useState("");
  const [maxConsecutiveHomeDays, setMaxConsecutiveHomeDays] = useState("");
  const [minBaseBlockDays, setMinBaseBlockDays] = useState("");
  const [minRequiredSoldiersPerDay, setMinRequiredSoldiersPerDay] = useState("");
  const [maxTotalHomeDays, setMaxTotalHomeDays] = useState(""); // שדה אופציונלי

  const handleCreateSchedulingRun = async () => {
    // בדיקה שכל השדות הנדרשים מלאים
    if (
      !startDate ||
      !endDate ||
      !defaultBaseDaysTarget ||
      !defaultHomeDaysTarget ||
      !maxConsecutiveBaseDays ||
      !maxConsecutiveHomeDays ||
      !minBaseBlockDays ||
      !minRequiredSoldiersPerDay
    ) {
      Alert.alert("חסרים שדות", "אנא מלא את כל השדות הנדרשים לפני יצירת שיבוץ.");
      return;
    }

    // ולידציה בסיסית של תאריכים
    if (new Date(startDate) >= new Date(endDate)) {
        Alert.alert("שגיאת תאריכים", "תאריך התחלה חייב להיות לפני תאריך סיום.");
        return;
    }

    try {
      // קריאה לשירות עם הנתונים המותאמים למודל SchedulingRun
      await schedulingService.runNewScheduling({
        start_date: startDate,
        end_date: endDate,
        default_base_days_target: Number(defaultBaseDaysTarget),
        default_home_days_target: Number(defaultHomeDaysTarget),
        max_consecutive_base_days: Number(maxConsecutiveBaseDays),
        max_consecutive_home_days: Number(maxConsecutiveHomeDays),
        min_base_block_days: Number(minBaseBlockDays),
        min_required_soldiers_per_day: Number(minRequiredSoldiersPerDay),
        // שדה אופציונלי - יש לשלוח רק אם הוזן ערך
        max_total_home_days: maxTotalHomeDays ? Number(maxTotalHomeDays) : null,
      });

      Alert.alert("שיבוץ נוצר בהצלחה!", "השיבוץ החדש נוצר ומופעל.");
      router.push("/"); // חזרה למסך הבית או למסך אחר

      // ניקוי הטופס לאחר שליחה מוצלחת
      setStartDate("");
      setEndDate("");
      setDefaultBaseDaysTarget("");
      setDefaultHomeDaysTarget("");
      setMaxConsecutiveBaseDays("");
      setMaxConsecutiveHomeDays("");
      setMinBaseBlockDays("");
      setMinRequiredSoldiersPerDay("");
      setMaxTotalHomeDays("");
    } catch (error:any) {
      console.error("שגיאה ביצירת שיבוץ:", error.response?.data || error.message);
      Alert.alert(
        "שגיאה ביצירת שיבוץ",
        "אירעה שגיאה בעת יצירת השיבוץ. אנא נסה שוב."
      );
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.scrollContainer} style={styles.container}>
      <Text style={styles.label}>תאריך התחלה (YYYY-MM-DD)*</Text>
      <TextInput
        style={styles.input}
        value={startDate}
        onChangeText={setStartDate}
        placeholder="לדוגמה: 2025-07-20"
        keyboardType="numbers-and-punctuation" // מאפשר קו מפריד
      />

      <Text style={styles.label}>תאריך סיום (YYYY-MM-DD)*</Text>
      <TextInput
        style={styles.input}
        value={endDate}
        onChangeText={setEndDate}
        placeholder="לדוגמה: 2025-08-20"
        keyboardType="numbers-and-punctuation"
      />

      <Text style={styles.label}>יעד ימי בסיס (ברירת מחדל)*</Text>
      <TextInput
        style={styles.input}
        value={defaultBaseDaysTarget}
        onChangeText={setDefaultBaseDaysTarget}
        keyboardType="numeric"
      />

      <Text style={styles.label}>יעד ימי בית (ברירת מחדל)*</Text>
      <TextInput
        style={styles.input}
        value={defaultHomeDaysTarget}
        onChangeText={setDefaultHomeDaysTarget}
        keyboardType="numeric"
      />

      <Text style={styles.label}>מקסימום ימי בסיס רצופים*</Text>
      <TextInput
        style={styles.input}
        value={maxConsecutiveBaseDays}
        onChangeText={setMaxConsecutiveBaseDays}
        keyboardType="numeric"
      />

      <Text style={styles.label}>מקסימום ימי בית רצופים*</Text>
      <TextInput
        style={styles.input}
        value={maxConsecutiveHomeDays}
        onChangeText={setMaxConsecutiveHomeDays}
        keyboardType="numeric"
      />

      <Text style={styles.label}>מינימום ימים בבלוק בסיס*</Text>
      <TextInput
        style={styles.input}
        value={minBaseBlockDays}
        onChangeText={setMinBaseBlockDays}
        keyboardType="numeric"
      />

      <Text style={styles.label}>מינימום חיילים נדרשים ביום*</Text>
      <TextInput
        style={styles.input}
        value={minRequiredSoldiersPerDay}
        onChangeText={setMinRequiredSoldiersPerDay}
        keyboardType="numeric"
      />

      <Text style={styles.label}>מקסימום ימי בית כוללים (אופציונלי)</Text>
      <TextInput
        style={styles.input}
        value={maxTotalHomeDays}
        onChangeText={setMaxTotalHomeDays}
        keyboardType="numeric"
        placeholder="השאר ריק אם אין הגבלה"
      />

      <TouchableOpacity onPress={handleCreateSchedulingRun}>
        <AntDesign style={styles.plusButton} name="pluscircle" size={40} color="black" />
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  scrollContainer: {
    padding: 20,
    paddingTop: 10,
  },
  label: {
    fontSize: 16,
    marginBottom: 5,
    marginTop: 10,
    fontWeight: 'bold',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    marginBottom: 5,
    borderRadius: 8,
    fontSize: 16,
  },
  plusButton: {
    alignSelf: "center",
    marginTop: 20,
    marginBottom: 20,
  },
});
















// import AntDesign from "@expo/vector-icons/AntDesign";
// import { useState } from "react";
// import { View, StyleSheet, TouchableOpacity, Text, TextInput, Alert, ScrollView } from "react-native";
// import { useRouter } from "expo-router";
// import { schedulingService } from "@/service/api";

// export default function EventForm() {
//   const router = useRouter();

//   const [evName, setEvName] = useState('');
//   const [startDate, setStartDate] = useState('');
//   const [endDate, setEndDate] = useState('');
//   const [maxHomeDays, setMaxHomeDays] = useState('');
//   const [minSol, setMinSol] = useState('');
//   const [baseDaysDiff, setBaseDaysDiff] = useState('');
//   const [homeDaysDiff, setHomeDaysDiff] = useState('');

//   const handleCreateEvent = async () => {
//     if (!evName || !startDate || !endDate || !maxHomeDays || !minSol || !baseDaysDiff || !homeDaysDiff) {
//       Alert.alert("חסרים שדות", "אנא מלא את כל השדות לפני יצירת אירוע.");
//       return;
//     }

//     try {
//       await schedulingService.runNewScheduling({
//         name: evName,
//         start_date: startDate,
//         end_date: endDate,
//         max_home_days: Number(maxHomeDays),
//         min_soldiers_req: Number(minSol),
//         base_days_diff: Number(baseDaysDiff),
//         home_days_diff: Number(homeDaysDiff),
//       });

//       Alert.alert('האירוע נוצר בהצלחה!');
//       router.push('/');

//       // ניקוי הטופס
//       setEvName('');
//       setStartDate('');
//       setEndDate('');
//       setMaxHomeDays('');
//       setMinSol('');
//       setBaseDaysDiff('');
//       setHomeDaysDiff('');
//     } catch (error) {
//       console.error("Error creating event:", error);
//       Alert.alert('שגיאה ביצירת האירוע');
//     }
//   };

//   return (
//     <ScrollView style={styles.container}>
//       <Text>Event Name</Text>
//       <TextInput style={styles.input} value={evName} onChangeText={setEvName} placeholder="שם האירוע" />

//       <Text>Start Date (YYYY-MM-DD)</Text>
//       <TextInput style={styles.input} value={startDate} onChangeText={setStartDate} placeholder="2025-07-20" />

//       <Text>End Date (YYYY-MM-DD)</Text>
//       <TextInput style={styles.input} value={endDate} onChangeText={setEndDate} placeholder="2025-08-20" />

//       <Text>default_base_days_target</Text>
//       <TextInput style={styles.input} value={maxHomeDays} onChangeText={setMaxHomeDays} keyboardType="numeric" />

//       <Text>max_consecutive_base_days</Text>
//       <TextInput style={styles.input} value={minSol} onChangeText={setMinSol} keyboardType="numeric" />

//       <Text>max_consecutive_home_days</Text>
//       <TextInput style={styles.input} value={baseDaysDiff} onChangeText={setBaseDaysDiff} keyboardType="numeric" />

//       <Text>min_base_block_days</Text>
//       <TextInput style={styles.input} value={homeDaysDiff} onChangeText={setHomeDaysDiff} keyboardType="numeric" />

//       <Text>min_required_soldiers_per_day</Text>
//       <TextInput style={styles.input} value={homeDaysDiff} onChangeText={setHomeDaysDiff} keyboardType="numeric" />

//       <Text>max_total_home_days</Text>
//       <TextInput style={styles.input} value={homeDaysDiff} onChangeText={setHomeDaysDiff} keyboardType="numeric" />

//       <TouchableOpacity onPress={handleCreateEvent}>
//         <AntDesign style={styles.plusButton} name="pluscircle" size={40} color="black" />
//       </TouchableOpacity>
//     </ScrollView>
//   );
// }

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     padding: 20,
//     marginTop: 1,
//     backgroundColor: "#fff",
//   },
//   input: {
//     borderWidth: 1,
//     padding: 10,
//     marginBottom: 10,
//     borderRadius: 8,
//     fontSize: 16,
//   },
//   plusButton: {
//     alignSelf: 'center',
//     marginTop: 5,
//   },
// });
















// // import { createEvent } from '@/service/api'; // ← עדיף להפריד את הקבצים
// // import AntDesign from '@expo/vector-icons/AntDesign';
// // import { useState } from 'react';
// // import { View, StyleSheet, TouchableOpacity, Text, TextInput, Alert } from 'react-native';
// // import { useRouter } from 'expo-router';

// // export default function EventForm() {
// //   const router = useRouter();

// //   const [evName, setEvName] = useState('');
// //   const [startDate, setStartDate] = useState('');
// //   const [endDate, setEndDate] = useState('');
// //   const [maxHomeDays, setMaxHomeDays] = useState('');
// //   const [minSol, setMinSol] = useState('');
// //   const [baseDaysDiff, setBaseDaysDiff] = useState('');
// //   const [homeDaysDiff, setHomeDaysDiff] = useState('');

// //   const handleCreateEvent = async () => {
// //     try {
// //       await createEvent({
// //         name: evName,
// //         start_date: startDate,
// //         end_date: endDate,
// //         max_home_days: Number(maxHomeDays),
// //         min_soldiers_req: Number(minSol),
// //         base_days_diff: Number(baseDaysDiff),
// //         home_days_diff: Number(homeDaysDiff),
// //       });
// //       Alert.alert('האירוע נוצר בהצלחה!');
// //       router.push('/'); // חזרה למסך הבית
// //     } catch (error) {
// //       Alert.alert('שגיאה ביצירת האירוע');
// //     }
// //   };

// //   return (
// //     <View style={styles.container}>
// //       <Text>Event Name</Text>
// //       <TextInput style={styles.input} value={evName} onChangeText={setEvName} />

// //       <Text>Start Date (YYYY-MM-DD)</Text>
// //       <TextInput style={styles.input} value={startDate} onChangeText={setStartDate} />

// //       <Text>End Date (YYYY-MM-DD)</Text>
// //       <TextInput style={styles.input} value={endDate} onChangeText={setEndDate} />

// //       <Text>Max Days at Home</Text>
// //       <TextInput style={styles.input} value={maxHomeDays} onChangeText={setMaxHomeDays} keyboardType="numeric" />

// //       <Text>Min Soldiers Required</Text>
// //       <TextInput style={styles.input} value={minSol} onChangeText={setMinSol} keyboardType="numeric" />

// //       <Text>Number of Base Days</Text>
// //       <TextInput style={styles.input} value={baseDaysDiff} onChangeText={setBaseDaysDiff} keyboardType="numeric" />

// //       <Text>Number of Home Days</Text>
// //       <TextInput style={styles.input} value={homeDaysDiff} onChangeText={setHomeDaysDiff} keyboardType="numeric" />

// //       <TouchableOpacity onPress={handleCreateEvent}>
// //         <AntDesign style={styles.plusButton} name="pluscircle" size={40} color="black" />
// //       </TouchableOpacity>
// //     </View>
// //   );
// // }

// // const styles = StyleSheet.create({
// //   container: {
// //     flex: 1,
// //     padding: 20,
// //     marginTop: 40,
// //   },
// //   input: {
// //     borderWidth: 1,
// //     padding: 10,
// //     marginBottom: 10,
// //     borderRadius: 8,
// //   },
// //   plusButton: {
// //     alignSelf: 'center',
// //     marginTop: 20,
// //   },
// // });
