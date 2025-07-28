import {
  getSchedulingRunById,
  getDetailedSchedule,
  schedulingService,
  soldierService, // ייבוא soldierService
} from "@/service/api";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState, useCallback } from "react";
import {
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  FlatList,
  Alert,
  Modal, // ייבוא Modal
} from "react-native";
import CalendarView from "@/components/CalendarView";
import AntDesign from "@expo/vector-icons/AntDesign";
import debounce from "lodash.debounce";
import { Card, Title } from "react-native-paper";
import { format } from "date-fns";

interface Soldier {
  id: number;
  name: string;
}

interface Assignment {
  id: number;
  soldier: number;
  soldier_name: string;
  assignment_date: string;
  is_on_base: boolean;
}

interface SchedulingRun {
  id: number;
  run_date: string;
  start_date: string;
  end_date: string;
  default_base_days_target: number;
  default_home_days_target: number;
  max_consecutive_base_days: number;
  max_consecutive_home_days: number;
  min_base_block_days: number;
  min_required_soldiers_per_day: number;
  max_total_home_days: number | null;
  status: string;
  solution_details: string;
  assignments: Assignment[];
}

interface DailyScheduleInfo {
  date: string;
  soldiers_on_base: string[];
  soldiers_at_home: string[];
}

export default function SchedulingRunDetails() {
  const { id } = useLocalSearchParams();
  const schedulingRunId = Number(id);
  const [schedulingRun, setSchedulingRun] = useState<SchedulingRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [dailyScheduleInfo, setDailyScheduleInfo] = useState<DailyScheduleInfo | null>(null);
  const [showParams, setShowParams] = useState(false);
  const [modalVisible, setModalVisible] = useState(false); // מצב לשליטה במודאל
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null); // חייל שנבחר מהרשימה

  const debouncedGetDailyScheduleInfo = useCallback(
    debounce(async (date: string) => {
      if (!schedulingRunId || isNaN(schedulingRunId)) return;
      try {
        const allDetailedSchedule: DailyScheduleInfo[] = await getDetailedSchedule(
          schedulingRunId
        );
        const infoForSelectedDate = allDetailedSchedule.find((item) => item.date === date);
        setDailyScheduleInfo(infoForSelectedDate || null);
      } catch (error) {
        console.error("Failed to fetch daily schedule info:", error);
        setDailyScheduleInfo(null);
      }
    }, 300),
    [schedulingRunId]
  );

  const handleDateSelect = (date: string) => {
    setSelectedDate(date);
    debouncedGetDailyScheduleInfo(date);
  };

  const fetchSchedulingRunData = async () => {
    if (!schedulingRunId || isNaN(schedulingRunId)) {
      setLoading(false);
      return;
    }
    try {
      const sr = await getSchedulingRunById(schedulingRunId);
      setSchedulingRun(sr as SchedulingRun);
    } catch (e) {
      console.error("Error fetching scheduling run details:", e);
      Alert.alert("Error", "Could not load scheduling run details.");
      setSchedulingRun(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedulingRunData();
    return () => {
      debouncedGetDailyScheduleInfo.cancel();
    };
  }, [schedulingRunId, debouncedGetDailyScheduleInfo]);

  const handleRunYesterday = async () => {
    Alert.alert(
      "Run Scheduling Again",
      "Are you sure you want to re-run scheduling with current parameters?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Run",
          onPress: async () => {
            if (!schedulingRun) {
              Alert.alert("Error", "No scheduling data found to re-run.");
              return;
            }

            const startDate = schedulingRun.start_date;
            const endDate = schedulingRun.end_date;

            const updateParams = {
              scheduling_run_id: schedulingRun.id,
              start_date: startDate,
              end_date: endDate,
              default_base_days_target: schedulingRun.default_base_days_target,
              default_home_days_target: schedulingRun.default_home_days_target,
              max_consecutive_base_days: schedulingRun.max_consecutive_base_days,
              max_consecutive_home_days: schedulingRun.max_consecutive_home_days,
              min_base_block_days: schedulingRun.min_base_block_days,
              min_required_soldiers_per_day: schedulingRun.min_required_soldiers_per_day,
              max_total_home_days: schedulingRun.max_total_home_days,
            };

            try {
              Alert.alert("Starting Run", "Running new schedule...");
              await schedulingService.updateExistingSchedulingRun(updateParams);
              Alert.alert("Success", "Schedule activated successfully!");
              fetchSchedulingRunData();
            } catch (error) {
              console.error("Error running schedule:", error);
              Alert.alert("Error", "Failed to run schedule again.");
            }
          },
        },
      ]
    );
  };

  const handleAddSoldier = () => {
    router.push({ pathname: '/event/AddSoldier' });
  };

  // פונקציה לטיפול בלחיצה על כרטיס חייל
  const handleSoldierPress = async (soldier: Soldier) => {
    setSelectedSoldier(soldier);
    setModalVisible(true);
  };

  // פונקציה לטיפול באופציה "הוסף שיבוץ"
  const handleAddAssignmentOption = async () => {
    setModalVisible(false); // סגור את המודאל
    if (selectedSoldier) {
      // נניח שאתה רוצה להוסיף שיבוץ לתאריך ספציפי או לבחור אותו
      // כאן פשוט נדחוף למסך הוספת שיבוץ עם ה-ID של החייל
      router.push({
        pathname: '/AddAssignmentScreen', // שנה לנתיב המתאים למסך הוספת שיבוץ
        params: { soldierId: selectedSoldier.id, soldierName: selectedSoldier.name, schedulingRunId: schedulingRunId, selectedDate: selectedDate || '' },
      });
    }
  };

  // פונקציה לטיפול באופציה "ערוך שיבוץ"
  const handleEditAssignmentOption = async () => {
    setModalVisible(false); // סגור את המודאל
    if (selectedSoldier && selectedDate) {
      // כאן נצטרך לשלוף את השיבוצים הקיימים של החייל לתאריך הנבחר
      // ונשלח אותם למסך העריכה.
      // לשם פשטות הדוגמה, נניח שיש לנו שירות ששולף שיבוצים של חייל לתאריך.
      try {
        const assignments = await schedulingService.getDetailedSchedule(schedulingRunId);
        // צריך למצוא את השיבוץ הספציפי ששייך לחייל ולתאריך הנבחר
        // נניח לצורך הדוגמה שיש לנו רק שיבוץ אחד לכל חייל ביום
        const relevantAssignment = schedulingRun?.assignments.find(
          (assignment) =>
            assignment.soldier_name === selectedSoldier.name &&
            assignment.assignment_date === selectedDate
        );

        if (relevantAssignment) {
        router.push({
          pathname: '/EditAssignmentScreen', // ודא שהנתיב נכון, כפי שדיברנו
          params: {
            assignmentId: relevantAssignment.id,
            soldierId: selectedSoldier.id,
            soldierName: selectedSoldier.name,
            assignmentDate: relevantAssignment.assignment_date,
            isOnBase: relevantAssignment.is_on_base.toString(), 
            schedulingRunId: schedulingRunId,
          },
        });
          
        } else {
          Alert.alert("No Assignment", "No assignment found for this soldier on the selected date.");
        }
      } catch (error) {
        console.error("Error fetching assignment for edit:", error);
        Alert.alert("Error", "Could not fetch assignment details for editing.");
      }
    } else {
      Alert.alert("Missing Info", "Please select a soldier and a date to edit an assignment.");
    }
  };


  if (loading) {
    return (
      <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />
    );
  }

  if (!schedulingRun) {
    return (
      <View style={styles.centeredContainer}>
        <Text style={styles.errorText}>Scheduling run not found or error loading.</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const uniqueSoldiers: Soldier[] = Array.from(
    new Set(schedulingRun.assignments.map((assignment) => assignment.soldier_name))
  ).map((soldierName, index) => ({ id: index, name: soldierName })); // ID כאן הוא זמני ולא מייצג את ה-ID האמיתי מה-backend. נצטרך לשלוף את ה-ID האמיתי.

  // פונקציה לשליפת ה-ID האמיתי של חייל על פי שמו
  const getSoldierIdFromName = async (soldierName: string): Promise<number | null> => {
    try {
      const allSoldiers: any[] = await soldierService.getAllSoldiers();
      const foundSoldier = allSoldiers.find(s => s.name === soldierName);
      return foundSoldier ? foundSoldier.id : null;
    } catch (error) {
      console.error("Error fetching soldier ID by name:", error);
      return null;
    }
  };

  const renderSoldier = ({ item }: { item: Soldier }) => (
    <TouchableOpacity onPress={async () => {
      // לפני ששולחים את החייל ל-handleSoldierPress, נשלוף את ה-ID האמיתי שלו
      const actualSoldierId = await getSoldierIdFromName(item.name);
      if (actualSoldierId !== null) {
        handleSoldierPress({ ...item, id: actualSoldierId }); // מעדכנים את ה-ID של החייל
      } else {
        Alert.alert("Error", "Could not find soldier ID.");
      }
    }}>
      <Card style={styles.card} elevation={2}>
        <Card.Content>
          <Title style={styles.cardTitle}>{item.name}</Title>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  const ListHeader = () => (
    <View>
      <TouchableOpacity onPress={handleRunYesterday} style={styles.runYesterdayButton}>
        <Text style={styles.runYesterdayButtonText}>הרץ מחדש 🔄</Text>
      </TouchableOpacity>

      <Text style={styles.schedulingRunName}>פרטי הרצת שיבוץ: #{schedulingRun.id}</Text>
      <Text style={styles.schedulingRunDateRange}>
        מתאריך: **{format(new Date(schedulingRun.start_date), 'dd/MM/yyyy')}** עד: **{format(new Date(schedulingRun.end_date), 'dd/MM/yyyy')}**
      </Text>
      <Text style={styles.schedulingRunStatus}>סטטוס: {schedulingRun.status}</Text>
      {schedulingRun.solution_details && (
        <Text style={styles.schedulingRunDetails}>
          **פרטי פתרון**: {schedulingRun.solution_details}
        </Text>
      )}

      <TouchableOpacity onPress={() => setShowParams(!showParams)} style={styles.toggleParamsButton}>
        <Text style={styles.toggleParamsButtonText}>
          {showParams ? "הסתר פרמטרים 🔼" : "הצג פרמטרים 🔽"}
        </Text>
      </TouchableOpacity>

      {showParams && (
        <View style={styles.paramsContainer}>
          <Text style={styles.paramText}>יעד ימי בסיס: **{schedulingRun.default_base_days_target}**</Text>
          <Text style={styles.paramText}>יעד ימי בית: **{schedulingRun.default_home_days_target}**</Text>
          <Text style={styles.paramText}>מקסימום ימי בסיס רצופים: **{schedulingRun.max_consecutive_base_days}**</Text>
          <Text style={styles.paramText}>מקסימום ימי בית רצופים: **{schedulingRun.max_consecutive_home_days}**</Text>
          <Text style={styles.paramText}>מינימום ימים בבלוק בסיס: **{schedulingRun.min_base_block_days}**</Text>
          <Text style={styles.paramText}>מינימום חיילים נדרשים ביום: **{schedulingRun.min_required_soldiers_per_day}**</Text>
          {schedulingRun.max_total_home_days !== null && (
            <Text style={styles.paramText}>מקסימום ימי בית כוללים: **{schedulingRun.max_total_home_days}**</Text>
          )}
        </View>
      )}

      <CalendarView
        startDate={schedulingRun.start_date}
        endDate={schedulingRun.end_date}
        selectedDate={selectedDate}
        onDateSelect={handleDateSelect}
      />

      {/* פרטי היום הנבחר - הועבר לכאן */}
      {selectedDate && dailyScheduleInfo ? (
        <View style={styles.dayInfo}>
          <Text style={styles.dayInfoTitle}>📅 פרטי יום: {format(new Date(dailyScheduleInfo.date), 'dd/MM/yyyy')}</Text>
          <Text style={styles.dayInfoText}>
            🪖 **בבסיס** ({dailyScheduleInfo.soldiers_on_base.length}):{" "}
            {dailyScheduleInfo.soldiers_on_base.join(", ") || "אין חיילים בבסיס."}
          </Text>
          <Text style={styles.dayInfoText}>
            🏠 **בבית** ({dailyScheduleInfo.soldiers_at_home.length}):{" "}
            {dailyScheduleInfo.soldiers_at_home.join(", ") || "אין חיילים בבית."}
          </Text>
        </View>
      ) : selectedDate && !dailyScheduleInfo && !loading ? (
        <View style={styles.dayInfo}>
          <Text style={styles.dayInfoText}>אין מידע עבור תאריך זה בשיבוץ הנבחר.</Text>
        </View>
      ) : null}

      {/* כפתור הוספת חייל - נשאר כאן כי הוא כללי לשיבוץ */}
      <Text style={styles.sectionHeader}>הוסף חייל חדש למערכת</Text>
      <TouchableOpacity onPress={handleAddSoldier} style={styles.plusButtonContainer}>
        <AntDesign name="pluscircle" size={40} color="#6200ee" />
      </TouchableOpacity>

      {/* כותרת רשימת החיילים */}
      {uniqueSoldiers.length > 0 && (
        <Text style={styles.sectionHeader}>חיילים בשיבוץ זה</Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={uniqueSoldiers}
        renderItem={renderSoldier}
        keyExtractor={(item) => item.id.toString()} // חשוב: נצטרך לשפר את זה בהמשך
        ListHeaderComponent={ListHeader}
        contentContainerStyle={styles.flatListContentContainer}
        showsVerticalScrollIndicator={false}
      />

      {/* מודאל לבחירת פעולה על חייל */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPressOut={() => setModalVisible(false)} // סגור מודאל בלחיצה מחוץ לו
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>בחר פעולה עבור {selectedSoldier?.name}</Text>
            <TouchableOpacity
              style={styles.modalButton}
              onPress={handleAddAssignmentOption}
            >
              <Text style={styles.modalButtonText}>➕ הוסף שיבוץ</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.modalButton}
              onPress={handleEditAssignmentOption}
            >
              <Text style={styles.modalButtonText}>✏️ ערוך שיבוץ</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalCancelButton]}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.modalButtonText}>ביטול</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  flatListContentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  centeredContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
  },
  loading: { flex: 1, justifyContent: "center", alignItems: "center" },
  errorText: {
    fontSize: 18,
    color: "#d32f2f",
    textAlign: "center",
    marginTop: 50,
  },
  backButton: {
    marginTop: 20,
    padding: 12,
    backgroundColor: "#e0e0e0",
    borderRadius: 8,
    alignSelf: "center",
  },
  backButtonText: {
    color: "#333",
    fontSize: 16,
    fontWeight: "600",
  },
  sectionHeader: {
    fontSize: 20,
    fontWeight: "bold",
    textAlign: "center",
    marginTop: 25,
    marginBottom: 15,
    color: "#3f51b5",
  },
  plusButtonContainer: {
    alignSelf: "center",
    marginBottom: 20,
  },
  schedulingRunName: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 8,
    color: "#6200ee",
    marginTop: 20,
  },
  schedulingRunDateRange: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 4,
    color: "#555",
  },
  schedulingRunStatus: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 10,
    color: "#555",
    fontStyle: "italic",
  },
  schedulingRunDetails: {
    fontSize: 14,
    textAlign: "center",
    marginBottom: 15,
    color: "#777",
    lineHeight: 20,
  },
  paramsContainer: {
    backgroundColor: "#e3f2fd",
    padding: 15,
    borderRadius: 10,
    marginTop: 10,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#bbdefb",
  },
  paramText: {
    fontSize: 14,
    marginBottom: 4,
    color: "#424242",
    lineHeight: 20,
  },
  dayInfo: {
    backgroundColor: "#e8f5e9",
    padding: 18,
    borderRadius: 12,
    marginTop: 25,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderLeftWidth: 5,
    borderLeftColor: "#4caf50",
  },
  dayInfoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#388e3c',
  },
  dayInfoText: {
    fontSize: 15,
    color: "#333",
    marginVertical: 3,
    lineHeight: 22,
  },
  card: {
    marginVertical: 4,
    backgroundColor: "#ffffff",
    borderRadius: 8,
    elevation: 3,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2.5,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#333",
    paddingVertical: 5,
  },
  toggleParamsButton: {
    backgroundColor: "#e0e0e0",
    padding: 10,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 15,
    marginBottom: 15,
  },
  toggleParamsButtonText: {
    fontSize: 15,
    fontWeight: "bold",
    color: "#444",
  },
  runYesterdayButton: {
    position: 'absolute',
    top: 0,
    right: 0,
    zIndex: 10,
    backgroundColor: '#ffecb3',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 3,
  },
  runYesterdayButtonText: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#6d4c41',
  },
  // סגנונות חדשים עבור המודאל
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)', // רקע שחור שקוף
  },
  modalContent: {
    backgroundColor: 'white',
    padding: 25,
    borderRadius: 15,
    elevation: 5,
    width: '80%',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
    textAlign: 'center',
  },
  modalButton: {
    backgroundColor: '#6200ee',
    padding: 15,
    borderRadius: 10,
    marginVertical: 8,
    width: '100%',
    alignItems: 'center',
  },
  modalButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalCancelButton: {
    backgroundColor: '#d32f2f', // אדום לביטול
    marginTop: 15,
  },
});















// import {
//   getSchedulingRunById,
//   getDetailedSchedule,
//   schedulingService,
// } from "@/service/api";
// import { router, useLocalSearchParams } from "expo-router";
// import React, { useEffect, useState, useCallback } from "react";
// import {
//   Text,
//   View,
//   TouchableOpacity,
//   ActivityIndicator,
//   StyleSheet,
//   FlatList,
//   Alert,
// } from "react-native";
// import CalendarView from "@/components/CalendarView";
// import AntDesign from "@expo/vector-icons/AntDesign";
// import debounce from "lodash.debounce";
// import { Card, Title } from "react-native-paper"; // Paragraph לא בשימוש
// import { format } from "date-fns";

// // הגדרת טיפוסים - נשארו כפי שהם, נראים בסדר
// interface Soldier {
//   id: number;
//   name: string;
// }

// interface Assignment {
//   id: number;
//   soldier: number;
//   soldier_name: string;
//   assignment_date: string;
//   is_on_base: boolean;
// }

// interface SchedulingRun {
//   id: number;
//   run_date: string;
//   start_date: string;
//   end_date: string;
//   default_base_days_target: number;
//   default_home_days_target: number;
//   max_consecutive_base_days: number;
//   max_consecutive_home_days: number;
//   min_base_block_days: number;
//   min_required_soldiers_per_day: number;
//   max_total_home_days: number | null;
//   status: string;
//   solution_details: string;
//   assignments: Assignment[];
// }

// interface DailyScheduleInfo {
//   date: string;
//   soldiers_on_base: string[];
//   soldiers_at_home: string[];
// }

// export default function SchedulingRunDetails() {
//   const { id } = useLocalSearchParams();
//   const schedulingRunId = Number(id);
//   const [schedulingRun, setSchedulingRun] = useState<SchedulingRun | null>(null);
//   const [loading, setLoading] = useState(true);
//   const [selectedDate, setSelectedDate] = useState<string | null>(null);
//   const [dailyScheduleInfo, setDailyScheduleInfo] = useState<DailyScheduleInfo | null>(null);
//   const [showParams, setShowParams] = useState(false);

//   // שימוש ב-useCallback ל-debounce כדי למנוע יצירה מחדש של הפונקציה
//   const debouncedGetDailyScheduleInfo = useCallback(
//     debounce(async (date: string) => {
//       if (!schedulingRunId || isNaN(schedulingRunId)) return;
//       try {
//         const allDetailedSchedule: DailyScheduleInfo[] = await getDetailedSchedule(
//           schedulingRunId
//         );
//         const infoForSelectedDate = allDetailedSchedule.find((item) => item.date === date);
//         setDailyScheduleInfo(infoForSelectedDate || null);
//       } catch (error) {
//         console.error("נכשל לשלוף מידע ליום נבחר:", error);
//         setDailyScheduleInfo(null);
//       }
//     }, 300),
//     [schedulingRunId] // תלויות עבור useCallback
//   );

//   const handleDateSelect = (date: string) => {
//     setSelectedDate(date);
//     debouncedGetDailyScheduleInfo(date);
//   };

//   const fetchSchedulingRunData = async () => {
//     if (!schedulingRunId || isNaN(schedulingRunId)) {
//       setLoading(false);
//       return;
//     }
//     try {
//       const sr = await getSchedulingRunById(schedulingRunId);
//       setSchedulingRun(sr as SchedulingRun);
//     } catch (e) {
//       console.error("שגיאה בשליפת פרטי הרצת שיבוץ:", e);
//       Alert.alert("שגיאה", "לא ניתן לטעון את פרטי השיבוץ.");
//       setSchedulingRun(null);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchSchedulingRunData();
//     return () => {
//       // ביטול ה-debounce בפירוק הקומפוננטה
//       debouncedGetDailyScheduleInfo.cancel();
//     };
//   }, [schedulingRunId, debouncedGetDailyScheduleInfo]); // הוספת debouncedGetDailyScheduleInfo לתלויות

//   const handleRunYesterday = async () => {
//     Alert.alert(
//       "הרץ שיבוץ מחדש",
//       "האם אתה בטוח שברצונך להריץ מחדש שיבוץ עם הפרמטרים הנוכחיים?",
//       [
//         { text: "ביטול", style: "cancel" },
//         {
//           text: "הרץ",
//           onPress: async () => {
//             if (!schedulingRun) {
//               Alert.alert("שגיאה", "לא נמצאו נתוני שיבוץ להרצה מחדש.");
//               return;
//             }

//             // עדכון תאריכי התחלה וסיום לתאריכים הדינמיים מה-schedulingRun
//             const startDate = schedulingRun.start_date;
//             const endDate = schedulingRun.end_date;

//             const updateParams = {
//               run_id: schedulingRun.id,
//               start_date: startDate, // שימוש בתאריך ההתחלה הקיים
//               end_date: endDate,     // שימוש בתאריך הסיום הקיים
//               default_base_days_target: schedulingRun.default_base_days_target,
//               default_home_days_target: schedulingRun.default_home_days_target,
//               max_consecutive_base_days: schedulingRun.max_consecutive_base_days,
//               max_consecutive_home_days: schedulingRun.max_consecutive_home_days,
//               min_base_block_days: schedulingRun.min_base_block_days,
//               min_required_soldiers_per_day: schedulingRun.min_required_soldiers_per_day,
//               max_total_home_days: schedulingRun.max_total_home_days,
//             };

//             try {
//               Alert.alert("התחלת הרצה", "מריץ שיבוץ חדש...");
//               await schedulingService.updateExistingSchedulingRun(updateParams);
//               Alert.alert("הצלחה", "שיבוץ הופעל בהצלחה!");
//               fetchSchedulingRunData(); // רענן את הנתונים לאחר הרצה מוצלחת
//             } catch (error) {
//               console.error("שגיאה בהרצת שיבוץ:", error);
//               Alert.alert("שגיאה", "נכשל להריץ שיבוץ מחדש.");
//             }
//           },
//         },
//       ]
//     );
//   };

//   const handleAddSoldier = () => {
//     router.push({ pathname: '/event/AddSoldier' });
//   };

//   if (loading) {
//     return (
//       <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />
//     );
//   }

//   if (!schedulingRun) {
//     return (
//       <View style={styles.centeredContainer}>
//         <Text style={styles.errorText}>הרצת שיבוץ לא נמצאה או שגיאה בטעינה.</Text>
//         <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
//           <Text style={styles.backButtonText}>חזור</Text>
//         </TouchableOpacity>
//       </View>
//     );
//   }

//   const uniqueSoldiers: Soldier[] = Array.from(
//     new Set(schedulingRun.assignments.map((assignment) => assignment.soldier_name))
//   ).map((soldierName, index) => ({ id: index, name: soldierName }));

//   const renderSoldier = ({ item }: { item: Soldier }) => (
//     <Card style={styles.card} elevation={2}>
//       <Card.Content>
//         <Title style={styles.cardTitle}>{item.name}</Title>
//       </Card.Content>
//     </Card>
//   );

//   // יצירת ה-Header עבור ה-FlatList
//   const ListHeader = () => (
//     <View>
//       <TouchableOpacity onPress={handleRunYesterday} style={styles.runYesterdayButton}>
//         <Text style={styles.runYesterdayButtonText}>הרץ מחדש 🔄</Text>
//       </TouchableOpacity>

//       <Text style={styles.schedulingRunName}>פרטי הרצת שיבוץ: #{schedulingRun.id}</Text>
//       <Text style={styles.schedulingRunDateRange}>
//         מתאריך: **{format(new Date(schedulingRun.start_date), 'dd/MM/yyyy')}** עד: **{format(new Date(schedulingRun.end_date), 'dd/MM/yyyy')}**
//       </Text>
//       <Text style={styles.schedulingRunStatus}>סטטוס: {schedulingRun.status}</Text>
//       {schedulingRun.solution_details && (
//         <Text style={styles.schedulingRunDetails}>
//           **פרטי פתרון**: {schedulingRun.solution_details}
//         </Text>
//       )}

//       <TouchableOpacity onPress={() => setShowParams(!showParams)} style={styles.toggleParamsButton}>
//         <Text style={styles.toggleParamsButtonText}>
//           {showParams ? "הסתר פרמטרים 🔼" : "הצג פרמטרים 🔽"}
//         </Text>
//       </TouchableOpacity>

//       {showParams && (
//         <View style={styles.paramsContainer}>
//           <Text style={styles.paramText}>יעד ימי בסיס: **{schedulingRun.default_base_days_target}**</Text>
//           <Text style={styles.paramText}>יעד ימי בית: **{schedulingRun.default_home_days_target}**</Text>
//           <Text style={styles.paramText}>מקסימום ימי בסיס רצופים: **{schedulingRun.max_consecutive_base_days}**</Text>
//           <Text style={styles.paramText}>מקסימום ימי בית רצופים: **{schedulingRun.max_consecutive_home_days}**</Text>
//           <Text style={styles.paramText}>מינימום ימים בבלוק בסיס: **{schedulingRun.min_base_block_days}**</Text>
//           <Text style={styles.paramText}>מינימום חיילים נדרשים ביום: **{schedulingRun.min_required_soldiers_per_day}**</Text>
//           {schedulingRun.max_total_home_days !== null && (
//             <Text style={styles.paramText}>מקסימום ימי בית כוללים: **{schedulingRun.max_total_home_days}**</Text>
//           )}
//         </View>
//       )}

//       <CalendarView
//         startDate={schedulingRun.start_date}
//         endDate={schedulingRun.end_date}
//         selectedDate={selectedDate}
//         onDateSelect={handleDateSelect}
//       />

//       {/* כפתור הוספת חייל */}
//       <Text style={styles.sectionHeader}>הוסף חייל לשיבוץ</Text>
//       <TouchableOpacity onPress={handleAddSoldier} style={styles.plusButtonContainer}>
//         <AntDesign name="pluscircle" size={40} color="#6200ee" />
//       </TouchableOpacity>
//     </View>
//   );

//   // יצירת ה-Footer עבור ה-FlatList
//   const ListFooter = () => (
//     <View>
//       {selectedDate && dailyScheduleInfo ? (
//         <View style={styles.dayInfo}>
//           <Text style={styles.dayInfoTitle}>📅 פרטי יום: {format(new Date(dailyScheduleInfo.date), 'dd/MM/yyyy')}</Text>
//           <Text style={styles.dayInfoText}>
//             🪖 **בבסיס** ({dailyScheduleInfo.soldiers_on_base.length}):{" "}
//             {dailyScheduleInfo.soldiers_on_base.join(", ") || "אין חיילים בבסיס."}
//           </Text>
//           <Text style={styles.dayInfoText}>
//             🏠 **בבית** ({dailyScheduleInfo.soldiers_at_home.length}):{" "}
//             {dailyScheduleInfo.soldiers_at_home.join(", ") || "אין חיילים בבית."}
//           </Text>
//         </View>
//       ) : selectedDate && !dailyScheduleInfo && !loading ? (
//         <View style={styles.dayInfo}>
//           <Text style={styles.dayInfoText}>אין מידע עבור תאריך זה בשיבוץ הנבחר.</Text>
//         </View>
//       ) : null}
//     </View>
//   );

//   return (
//     <FlatList
//       data={uniqueSoldiers}
//       renderItem={renderSoldier}
//       keyExtractor={(item) => item.id.toString()}
//       ListHeaderComponent={ListHeader}
//       ListFooterComponent={ListFooter}
//       contentContainerStyle={styles.flatListContentContainer}
//       showsVerticalScrollIndicator={false}
//     />
//   );
// }

// const styles = StyleSheet.create({
//   container: { 
//     flex: 1, 
//     backgroundColor: "#f5f5f5", // רקע בהיר יותר
//   },
//   flatListContentContainer: {
//     padding: 20, // מרווח כללי מהצדדים
//     paddingBottom: 40, // מרווח בתחתית הרשימה
//   },
//   centeredContainer: {
//     flex: 1,
//     justifyContent: "center",
//     alignItems: "center",
//     backgroundColor: "#f5f5f5",
//   },
//   loading: { flex: 1, justifyContent: "center", alignItems: "center" },
//   errorText: {
//     fontSize: 18,
//     color: "#d32f2f", // אדום כהה יותר
//     textAlign: "center",
//     marginTop: 50,
//   },
//   backButton: {
//     marginTop: 20,
//     padding: 12,
//     backgroundColor: "#e0e0e0",
//     borderRadius: 8,
//     alignSelf: "center",
//   },
//   backButtonText: {
//     color: "#333",
//     fontSize: 16,
//     fontWeight: "600",
//   },
//   sectionHeader: { // כותרת כללית לסקציות
//     fontSize: 20,
//     fontWeight: "bold",
//     textAlign: "center",
//     marginTop: 25, // מרווח גדול יותר מעל כותרת סקציה
//     marginBottom: 15, // מרווח מתחת לכותרת סקציה
//     color: "#3f51b5", // צבע כחול-סגול
//   },
//   plusButtonContainer: { 
//     alignSelf: "center", 
//     marginBottom: 20, // מרווח נחמד מתחת לכפתור
//   },
//   schedulingRunName: {
//     fontSize: 24,
//     fontWeight: "bold",
//     textAlign: "center",
//     marginBottom: 8,
//     color: "#6200ee",
//     marginTop: 20, // מרווח מהכפתור העליון
//   },
//   schedulingRunDateRange: {
//     fontSize: 16,
//     textAlign: "center",
//     marginBottom: 4,
//     color: "#555",
//   },
//   schedulingRunStatus: {
//     fontSize: 16,
//     textAlign: "center",
//     marginBottom: 10,
//     color: "#555",
//     fontStyle: "italic",
//   },
//   schedulingRunDetails: {
//     fontSize: 14,
//     textAlign: "center",
//     marginBottom: 15,
//     color: "#777",
//     lineHeight: 20, // רווח שורות
//   },
//   paramsContainer: {
//     backgroundColor: "#e3f2fd", // רקע כחול בהיר
//     padding: 15,
//     borderRadius: 10,
//     marginTop: 10, // מרווח מהכפתור מעל
//     marginBottom: 20,
//     borderWidth: 1,
//     borderColor: "#bbdefb",
//   },
//   paramText: {
//     fontSize: 14,
//     marginBottom: 4, // מרווח קטן יותר בין פרמטרים
//     color: "#424242",
//     lineHeight: 20,
//   },
//   dayInfo: {
//     backgroundColor: "#e8f5e9", // ירוק בהיר
//     padding: 18,
//     borderRadius: 12,
//     marginTop: 25, // מרווח גדול יותר מהחלק הקודם
//     shadowColor: "#000",
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.1,
//     shadowRadius: 4,
//     elevation: 2,
//     borderLeftWidth: 5, // פס צבעוני בצד
//     borderLeftColor: "#4caf50",
//   },
//   dayInfoTitle: {
//     fontSize: 18,
//     fontWeight: 'bold',
//     marginBottom: 10,
//     color: '#388e3c',
//   },
//   dayInfoText: {
//     fontSize: 15,
//     color: "#333",
//     marginVertical: 3, // מרווח קטן יותר בין שורות
//     lineHeight: 22,
//   },
//   card: {
//     marginVertical: 4, // מרווח קטן יותר בין כרטיסים
//     backgroundColor: "#ffffff",
//     borderRadius: 8,
//     elevation: 3,
//     shadowColor: "#000",
//     shadowOffset: { width: 0, height: 1 },
//     shadowOpacity: 0.15, // צל עדין יותר
//     shadowRadius: 2.5,
//   },
//   cardTitle: {
//     fontSize: 17,
//     fontWeight: "600",
//     color: "#333",
//     paddingVertical: 5, // מרווח פנימי בכרטיס
//   },
//   toggleParamsButton: {
//     backgroundColor: "#e0e0e0",
//     padding: 10,
//     borderRadius: 8,
//     alignItems: "center",
//     marginTop: 15, // מרווח מהפרטים למעלה
//     marginBottom: 15, // מרווח מהפרמטרים למטה / קלנדר
//   },
//   toggleParamsButtonText: {
//     fontSize: 15,
//     fontWeight: "bold",
//     color: "#444",
//   },
//   runYesterdayButton: {
//     position: 'absolute',
//     top: 0, // מיקום יחסי לראש המסך
//     right: 0, // מיקום יחסי לימין המסך
//     zIndex: 10,
//     backgroundColor: '#ffecb3', // צהוב-כתום בהיר
//     paddingVertical: 6,
//     paddingHorizontal: 12,
//     borderRadius: 8,
//     shadowColor: "#000",
//     shadowOffset: { width: 0, height: 1 },
//     shadowOpacity: 0.2,
//     shadowRadius: 2,
//     elevation: 3,
//   },
//   runYesterdayButtonText: {
//     fontSize: 13,
//     fontWeight: 'bold',
//     color: '#6d4c41', // חום כהה
//   }
// });

















// // import {
// //   getSchedulingRunById,
// //   getDetailedSchedule,
// //   schedulingService, // ייבוא של schedulingService
// // } from "@/service/api"; // נתיב מעודכן
// // import { router, useLocalSearchParams } from "expo-router";
// // import React, { useEffect, useState } from "react";
// // import {
// //   Text,
// //   View,
// //   TouchableOpacity,
// //   ActivityIndicator,
// //   StyleSheet,
// //   FlatList,
// //   ScrollView,
// //   Alert, // נוסף לשימוש בהתראות
// // } from "react-native";
// // import CalendarView from "@/components/CalendarView";
// // import AntDesign from "@expo/vector-icons/AntDesign";
// // import debounce from "lodash.debounce";
// // import { Card, Title, Paragraph } from "react-native-paper";
// // import { format } from "date-fns"; // לייצוא תאריכים

// // // הגדרת טיפוסים מדויקת יותר שתואמת למודלים ב-Django
// // interface Soldier {
// //   id: number;
// //   name: string;
// // }

// // interface Assignment {
// //   id: number;
// //   soldier: number; // ID של החייל
// //   soldier_name: string; // שם החייל
// //   assignment_date: string; // תאריך השיבוץ
// //   is_on_base: boolean; // האם בבסיס
// // }

// // interface SchedulingRun {
// //   id: number;
// //   run_date: string;
// //   start_date: string;
// //   end_date: string;
// //   default_base_days_target: number;
// //   default_home_days_target: number;
// //   max_consecutive_base_days: number;
// //   max_consecutive_home_days: number;
// //   min_base_block_days: number;
// //   min_required_soldiers_per_day: number;
// //   max_total_home_days: number | null;
// //   status: string;
// //   solution_details: string;
// //   assignments: Assignment[]; // רשימת השיבוצים המקושרים
// // }

// // interface DailyScheduleInfo {
// //   date: string;
// //   soldiers_on_base: string[];
// //   soldiers_at_home: string[];
// //   // ניתן להוסיף כאן שדות נוספים אם ה-backend יחזיר אותם
// // }

// // export default function SchedulingRunDetails() {
// //   const { id } = useLocalSearchParams();
// //   const schedulingRunId = Number(id);
// //   const [schedulingRun, setSchedulingRun] = useState<SchedulingRun | null>(null);
// //   const [loading, setLoading] = useState(true);
// //   const [selectedDate, setSelectedDate] = useState<string | null>(null);
// //   const [dailyScheduleInfo, setDailyScheduleInfo] = useState<DailyScheduleInfo | null>(null);
// //   const [showParams, setShowParams] = useState(false); // מצב להצגת/הסתרת פרמטרים

// //   const debouncedGetDailyScheduleInfo = debounce(async (date: string) => {
// //     if (!schedulingRunId || isNaN(schedulingRunId)) return;
// //     try {
// //       const allDetailedSchedule: DailyScheduleInfo[] = await getDetailedSchedule(
// //         schedulingRunId
// //       );
// //       const infoForSelectedDate = allDetailedSchedule.find((item) => item.date === date);
// //       setDailyScheduleInfo(infoForSelectedDate || null);
// //     } catch (error) {
// //       console.error("נכשל לשלוף מידע ליום נבחר:", error);
// //       setDailyScheduleInfo(null);
// //     }
// //   }, 300);

// //   const handleDateSelect = (date: string) => {
// //     setSelectedDate(date);
// //     debouncedGetDailyScheduleInfo(date);
// //   };

// //   const fetchSchedulingRunData = async () => {
// //     if (!schedulingRunId || isNaN(schedulingRunId)) {
// //       setLoading(false);
// //       return;
// //     }
// //     try {
// //       const sr = await getSchedulingRunById(schedulingRunId);
// //       setSchedulingRun(sr as SchedulingRun);
// //     } catch (e) {
// //       console.error("שגיאה בשליפת פרטי הרצת שיבוץ:", e);
// //       Alert.alert("שגיאה", "לא ניתן לטעון את פרטי השיבוץ.");
// //       setSchedulingRun(null);
// //     } finally {
// //       setLoading(false);
// //     }
// //   };

// //   useEffect(() => {
// //     fetchSchedulingRunData();
// //     return () => {
// //       debouncedGetDailyScheduleInfo.cancel();
// //     };
// //   }, [schedulingRunId]);

// //   const handleRunYesterday = async () => {
// //     Alert.alert(
// //       "הרץ שיבוץ אתמול",
// //       "האם אתה בטוח שברצונך להריץ מחדש שיבוץ עבור אתמול עם הפרמטרים הנוכחיים?",
// //       [
// //         { text: "ביטול", style: "cancel" },
// //         {
// //           text: "הרץ",
// //           onPress: async () => {
// //             if (!schedulingRun) {
// //               Alert.alert("שגיאה", "לא נמצאו נתוני שיבוץ להרצה מחדש.");
// //               return;
// //             }

// //             const yesterday = new Date();
// //             yesterday.setDate(yesterday.getDate() - 1);
// //             const yesterdayDateString = format(yesterday, "yyyy-MM-dd");

// //             // יצירת אובייקט עם הפרמטרים הנדרשים ל-updateExistingSchedulingRun
// //             const updateParams = {
// //               run_id: schedulingRun.id, // ID של הרצת השיבוץ הקיימת
// //               start_date: "2025-07-25", // תאריך התחלה אתמול
// //               end_date: "2025-09-18", // תאריך סיום אתמול
// //               default_base_days_target: schedulingRun.default_base_days_target,
// //               default_home_days_target: schedulingRun.default_home_days_target,
// //               max_consecutive_base_days: schedulingRun.max_consecutive_base_days,
// //               max_consecutive_home_days: schedulingRun.max_consecutive_home_days,
// //               min_base_block_days: schedulingRun.min_base_block_days,
// //               min_required_soldiers_per_day: schedulingRun.min_required_soldiers_per_day,
// //               max_total_home_days: schedulingRun.max_total_home_days,
// //             };

// //             try {
// //               Alert.alert("התחלת הרצה", "מריץ שיבוץ חדש עבור אתמול...");
// //               await schedulingService.updateExistingSchedulingRun(updateParams);
// //               Alert.alert("הצלחה", "שיבוץ עבור אתמול הופעל בהצלחה!");
// //               // ניתן לרענן את הנתונים לאחר הרצה מוצלחת
// //               fetchSchedulingRunData();
// //             } catch (error) {
// //               console.error("שגיאה בהרצת שיבוץ לאתמול:", error);
// //               Alert.alert("שגיאה", "נכשל להריץ שיבוץ עבור אתמול.");
// //             }
// //           },
// //         },
// //       ]
// //     );
// //   };

// //   const handleAddSoldier = () => {
// //     router.push({pathname:'/event/AddSoldier'})
// //   };

// //   if (loading) {
// //     return (
// //       <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />
// //     );
// //   }

// //   if (!schedulingRun) {
// //     return (
// //       <View style={styles.container}>
// //         <Text style={styles.errorText}>הרצת שיבוץ לא נמצאה או שגיאה בטעינה.</Text>
// //         <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
// //           <Text style={styles.backButtonText}>חזור</Text>
// //         </TouchableOpacity>
// //       </View>
// //     );
// //   }

// //   const uniqueSoldiers: Soldier[] = Array.from(
// //     new Set(schedulingRun.assignments.map((assignment) => assignment.soldier_name))
// //   ).map((soldierName, index) => ({ id: index, name: soldierName }));

// //   const renderSoldier = ({ item }: { item: Soldier }) => (
// //     <Card style={styles.card} elevation={2}>
// //       <Card.Content>
// //         <Title>{item.name}</Title>
// //       </Card.Content>
// //     </Card>
// //   );

// //   return (
// //     <ScrollView style={styles.container}>
// //       {/* כפתור "הרץ אתמול" בפינה השמאלית העליונה */}
// //       <TouchableOpacity onPress={handleRunYesterday} style={styles.runYesterdayButton}>
// //         <Text style={styles.runYesterdayButtonText}>הרץ אתמול ↩️</Text>
// //       </TouchableOpacity>

// //       <Text style={styles.schedulingRunName}>פרטי הרצת שיבוץ: {schedulingRun.id}</Text>
// //       <Text style={styles.schedulingRunDateRange}>
// //         מתאריך: {schedulingRun.start_date} עד: {schedulingRun.end_date}
// //       </Text>
// //       <Text style={styles.schedulingRunStatus}>סטטוס: {schedulingRun.status}</Text>
// //       {schedulingRun.solution_details && (
// //         <Text style={styles.schedulingRunDetails}>
// //           פרטי פתרון: {schedulingRun.solution_details}
// //         </Text>
// //       )}

// //       {/* כפתור להצגה/הסתרת פרמטרים */}
// //       <TouchableOpacity onPress={() => setShowParams(!showParams)} style={styles.toggleParamsButton}>
// //         <Text style={styles.toggleParamsButtonText}>
// //           {showParams ? "הסתר פרמטרים 🔼" : "הצג פרמטרים 🔽"}
// //         </Text>
// //       </TouchableOpacity>

// //       {showParams && (
// //         <View style={styles.paramsContainer}>
// //           <Text style={styles.paramText}>יעד ימי בסיס: {schedulingRun.default_base_days_target}</Text>
// //           <Text style={styles.paramText}>יעד ימי בית: {schedulingRun.default_home_days_target}</Text>
// //           <Text style={styles.paramText}>מקסימום ימי בסיס רצופים: {schedulingRun.max_consecutive_base_days}</Text>
// //           <Text style={styles.paramText}>מקסימום ימי בית רצופים: {schedulingRun.max_consecutive_home_days}</Text>
// //           <Text style={styles.paramText}>מינימום ימים בבלוק בסיס: {schedulingRun.min_base_block_days}</Text>
// //           <Text style={styles.paramText}>מינימום חיילים נדרשים ביום: {schedulingRun.min_required_soldiers_per_day}</Text>
// //           {schedulingRun.max_total_home_days !== null && (
// //             <Text style={styles.paramText}>מקסימום ימי בית כוללים: {schedulingRun.max_total_home_days}</Text>
// //           )}
// //         </View>
// //       )}

// //       <CalendarView
// //         startDate={schedulingRun.start_date}
// //         endDate={schedulingRun.end_date}
// //         selectedDate={selectedDate}
// //         onDateSelect={handleDateSelect}
// //       />

// //       {/* כפתור הוספת חייל */}
// //       <Text style={styles.header}>הוסף חייל לשיבוץ</Text>
// //       <TouchableOpacity onPress={handleAddSoldier}>
// //         <AntDesign
// //           style={styles.plusButton}
// //           name="pluscircle"
// //           size={40}
// //           color="#6200ee"
// //         />
// //       </TouchableOpacity>

// //       {uniqueSoldiers.length > 0 && (
// //         <>
// //           <Text style={styles.header}>חיילים בשיבוץ זה</Text>
// //           <FlatList
// //             data={uniqueSoldiers}
// //             renderItem={renderSoldier}
// //             keyExtractor={(item) => item.id.toString()}
// //             style={styles.soldierList}
// //             contentContainerStyle={{ paddingBottom: 20 }}
// //             showsVerticalScrollIndicator={false}
// //           />
// //         </>
// //       )}

// //       {selectedDate && dailyScheduleInfo ? (
// //         <View style={styles.dayInfo}>
// //           <Text style={styles.dayInfoText}>
// //             📅 <Text style={{ fontWeight: "bold" }}>{dailyScheduleInfo.date}</Text>
// //           </Text>
// //           <Text style={styles.dayInfoText}>
// //             🪖 בבסיס ({dailyScheduleInfo.soldiers_on_base.length}):{" "}
// //             {dailyScheduleInfo.soldiers_on_base.join(", ") || "אין"}
// //           </Text>
// //           <Text style={styles.dayInfoText}>
// //             🏠 בבית ({dailyScheduleInfo.soldiers_at_home.length}):{" "}
// //             {dailyScheduleInfo.soldiers_at_home.join(", ") || "אין"}
// //           </Text>
// //         </View>
// //       ) : selectedDate && !dailyScheduleInfo && !loading ? (
// //         <View style={styles.dayInfo}>
// //           <Text style={styles.dayInfoText}>אין מידע עבור תאריך זה בשיבוץ הנבחר.</Text>
// //         </View>
// //       ) : null}
// //     </ScrollView>
// //   );
// // }

// // const styles = StyleSheet.create({
// //   container: { flex: 1, padding: 20, backgroundColor: "#fff" },
// //   loading: { flex: 1, justifyContent: "center", alignItems: "center" },
// //   errorText: {
// //     fontSize: 18,
// //     color: "red",
// //     textAlign: "center",
// //     marginTop: 50,
// //   },
// //   backButton: {
// //     marginTop: 20,
// //     padding: 10,
// //     backgroundColor: "#eee",
// //     borderRadius: 5,
// //     alignSelf: "center",
// //   },
// //   backButtonText: {
// //     color: "#333",
// //     fontSize: 16,
// //   },
// //   header: {
// //     fontSize: 20,
// //     fontWeight: "bold",
// //     textAlign: "center",
// //     marginBottom: 10,
// //     marginTop: 20,
// //     color: "#333",
// //   },
// //   plusButton: { alignSelf: "center", marginBottom: 20 },
// //   schedulingRunName: {
// //     fontSize: 22,
// //     fontWeight: "bold",
// //     textAlign: "center",
// //     marginBottom: 5,
// //     color: "#6200ee",
// //   },
// //   schedulingRunDateRange: {
// //     fontSize: 16,
// //     textAlign: "center",
// //     marginBottom: 5,
// //     color: "#555",
// //   },
// //   schedulingRunStatus: {
// //     fontSize: 16,
// //     textAlign: "center",
// //     marginBottom: 10,
// //     color: "#555",
// //     fontStyle: "italic",
// //   },
// //   schedulingRunDetails: {
// //     fontSize: 14,
// //     textAlign: "center",
// //     marginBottom: 15,
// //     color: "#777",
// //   },
// //   paramsContainer: {
// //     backgroundColor: "#f9f9f9",
// //     padding: 15,
// //     borderRadius: 10,
// //     marginBottom: 20,
// //     borderWidth: 1,
// //     borderColor: "#e0e0e0",
// //   },
// //   paramText: {
// //     fontSize: 14,
// //     marginBottom: 5,
// //     color: "#444",
// //   },
// //   dayInfo: {
// //     backgroundColor: "#f0f4f8",
// //     padding: 15,
// //     borderRadius: 10,
// //     marginTop: 20,
// //     shadowColor: "#000",
// //     shadowOffset: { width: 0, height: 2 },
// //     shadowOpacity: 0.1,
// //     shadowRadius: 4,
// //     elevation: 2,
// //   },
// //   dayInfoText: {
// //     fontSize: 15,
// //     color: "#333",
// //     marginVertical: 4,
// //     lineHeight: 24,
// //   },
// //   soldierList: {
// //     maxHeight: 320,
// //   },
// //   card: {
// //     marginVertical: 6,
// //     backgroundColor: "#fff",
// //     borderRadius: 8,
// //     elevation: 3,
// //     shadowColor: "#000",
// //     shadowOffset: { width: 0, height: 1 },
// //     shadowOpacity: 0.2,
// //     shadowRadius: 1.41,
// //   },
// //   toggleParamsButton: {
// //     backgroundColor: "#e0e0e0",
// //     padding: 10,
// //     borderRadius: 8,
// //     alignItems: "center",
// //     marginTop: 10,
// //     marginBottom: 10,
// //   },
// //   toggleParamsButtonText: {
// //     fontSize: 15,
// //     fontWeight: "bold",
// //     color: "#444",
// //   },
// //   runYesterdayButton: {
// //     position: 'absolute',
// //     top: 10,
// //     left: 10,
// //     zIndex: 10,
// //     backgroundColor: '#ffeb3b',
// //     paddingVertical: 5,
// //     paddingHorizontal: 10,
// //     borderRadius: 5,
// //     shadowColor: "#000",
// //     shadowOffset: { width: 0, height: 1 },
// //     shadowOpacity: 0.2,
// //     shadowRadius: 1.41,
// //     elevation: 2,
// //   },
// //   runYesterdayButtonText: {
// //     fontSize: 12,
// //     fontWeight: 'bold',
// //     color: '#333',
// //   }
// // });





















// // import { getSchedulingRunById, getDetailedSchedule } from "@/service/api"; // שינוי נתיב וייבוא ספציפי
// // import { router, useLocalSearchParams } from "expo-router";
// // import React, { useEffect, useState } from "react";
// // import {
// //   Text,
// //   View,
// //   TouchableOpacity,
// //   ActivityIndicator,
// //   StyleSheet,
// //   FlatList,
// //   ScrollView,
// //   Alert,
// // } from "react-native";
// // import CalendarView from "@/components/CalendarView";
// // import AntDesign from "@expo/vector-icons/AntDesign";
// // import debounce from "lodash.debounce";
// // import { Card, Title } from "react-native-paper";

// // // הגדרת טיפוסים מדויקת יותר שתואמת למודלים ב-Django
// // interface Soldier {
// //   id: number;
// //   name: string;
// // }

// // interface Assignment {
// //   id: number;
// //   soldier: number; // ID של החייל
// //   soldier_name: string; // שם החייל
// //   assignment_date: string; // תאריך השיבוץ
// //   is_on_base: boolean; // האם בבסיס
// // }

// // interface SchedulingRun {
// //   id: number;
// //   run_date: string;
// //   start_date: string;
// //   end_date: string;
// //   default_base_days_target: number;
// //   default_home_days_target: number;
// //   max_consecutive_base_days: number;
// //   max_consecutive_home_days: number;
// //   min_base_block_days: number;
// //   min_required_soldiers_per_day: number;
// //   max_total_home_days: number | null;
// //   status: string;
// //   solution_details: string;
// //   assignments: Assignment[]; // רשימת השיבוצים המקושרים
// // }

// // // טיפוס עבור המידע המפורט ליום ספציפי
// // interface DailyScheduleInfo {
// //   date: string;
// //   soldiers_on_base: string[];
// //   soldiers_at_home: string[];
// //   // אם ה-backend יחזיר שדות נוספים כמו going_home, returning, min_required, יש להוסיף אותם כאן
// //   // לדוגמה:
// //   // soldiers_going_home: string[];
// //   // soldiers_returning: string[];
// //   // min_required_on_base: number;
// // }

// // // נשנה את שם הקומפוננטה שתשקף שהיא מציגה SchedulingRun
// // export default function SchedulingRunDetails() {
// //   const { id } = useLocalSearchParams();
// //   const schedulingRunId = Number(id);
// //   const [schedulingRun, setSchedulingRun] = useState<SchedulingRun | null>(null);
// //   const [loading, setLoading] = useState(true);
// //   const [selectedDate, setSelectedDate] = useState<string | null>(null);
// //   const [dailyScheduleInfo, setDailyScheduleInfo] = useState<DailyScheduleInfo | null>(null);

// //   // פונקציית debounce עבור קריאת ה-API של פרטי יום ספציפי
// //   const debouncedGetDailyScheduleInfo = debounce(async (date: string) => {
// //     if (!schedulingRunId || isNaN(schedulingRunId)) return;
// //     try {
// //       // ה-API getDetailedSchedule מחזיר מערך של אובייקטים לכל יום בטווח.
// //       // אנחנו צריכים למצוא את האובייקט המתאים לתאריך הנבחר.
// //       const allDetailedSchedule: DailyScheduleInfo[] = await getDetailedSchedule(schedulingRunId);
// //       const infoForSelectedDate = allDetailedSchedule.find(item => item.date === date);
// //       setDailyScheduleInfo(infoForSelectedDate || null);
// //     } catch (error) {
// //       console.error("נכשל לשלוף מידע ליום נבחר:", error);
// //       setDailyScheduleInfo(null);
// //     }
// //   }, 300);

// //   const handleDateSelect = (date: string) => {
// //     setSelectedDate(date);
// //     debouncedGetDailyScheduleInfo(date);
// //   };

// //   useEffect(() => {
// //     if (!schedulingRunId || isNaN(schedulingRunId)) {
// //       setLoading(false);
// //       return;
// //     }

// //     const fetchSchedulingRun = async () => {
// //       try {
// //         const sr = await getSchedulingRunById(schedulingRunId);
// //         setSchedulingRun(sr as SchedulingRun); // ודא התאמת טיפוסים
// //       } catch (e) {
// //         console.error("שגיאה בשליפת פרטי הרצת שיבוץ:", e);
// //         Alert.alert('שגיאה', 'לא ניתן לטעון את פרטי השיבוץ.'); // הודעה למשתמש
// //         setSchedulingRun(null); // אפס את הנתונים במקרה של שגיאה
// //       } finally {
// //         setLoading(false);
// //       }
// //     };

// //     fetchSchedulingRun();

// //     return () => {
// //       debouncedGetDailyScheduleInfo.cancel();
// //     };
// //   }, [schedulingRunId]);

// //   if (loading) {
// //     return <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />;
// //   }

// //   if (!schedulingRun) {
// //     return (
// //       <View style={styles.container}>
// //         <Text style={styles.errorText}>הרצת שיבוץ לא נמצאה או שגיאה בטעינה.</Text>
// //         <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
// //             <Text style={styles.backButtonText}>חזור</Text>
// //         </TouchableOpacity>
// //       </View>
// //     );
// //   }

// //   // נאסוף רשימה ייחודית של חיילים מתוך השיבוצים כדי להציג אותם ב-FlatList
// //   // הפתרון הזה מניח ש-soldier_name תמיד יהיה קיים ב-assignment
// //   const uniqueSoldiers: Soldier[] = Array.from(
// //     new Set(schedulingRun.assignments.map(assignment => assignment.soldier_name))
// //   ).map((soldierName, index) => ({ id: index, name: soldierName }));

// //   const renderSoldier = ({ item }: { item: Soldier }) => ( // תיקון שגיאה 1003 כאן
// //     <Card style={styles.card} elevation={2}>
// //       <Card.Content>
// //         <Title>{item.name}</Title>
// //       </Card.Content>
// //     </Card>
// //   );

// //   return (
// //     <ScrollView style={styles.container}>
// //       <Text style={styles.schedulingRunName}>פרטי הרצת שיבוץ: {schedulingRun.id}</Text>
// //       <Text style={styles.schedulingRunDateRange}>
// //         מתאריך: {schedulingRun.start_date} עד: {schedulingRun.end_date}
// //       </Text>
// //       <Text style={styles.schedulingRunStatus}>סטטוס: {schedulingRun.status}</Text>
// //       {schedulingRun.solution_details && (
// //         <Text style={styles.schedulingRunDetails}>
// //           פרטי פתרון: {schedulingRun.solution_details}
// //         </Text>
// //       )}

// //       <View style={styles.paramsContainer}>
// //         <Text style={styles.paramText}>יעד ימי בסיס: {schedulingRun.default_base_days_target}</Text>
// //         <Text style={styles.paramText}>יעד ימי בית: {schedulingRun.default_home_days_target}</Text>
// //         <Text style={styles.paramText}>מקסימום ימי בסיס רצופים: {schedulingRun.max_consecutive_base_days}</Text>
// //         <Text style={styles.paramText}>מקסימום ימי בית רצופים: {schedulingRun.max_consecutive_home_days}</Text>
// //         <Text style={styles.paramText}>מינימום ימים בבלוק בסיס: {schedulingRun.min_base_block_days}</Text>
// //         <Text style={styles.paramText}>מינימום חיילים נדרשים ביום: {schedulingRun.min_required_soldiers_per_day}</Text>
// //         {schedulingRun.max_total_home_days !== null && (
// //           <Text style={styles.paramText}>מקסימום ימי בית כוללים: {schedulingRun.max_total_home_days}</Text>
// //         )}
// //       </View>

// //       <CalendarView
// //         startDate={schedulingRun.start_date}
// //         endDate={schedulingRun.end_date}
// //         selectedDate={selectedDate}
// //         onDateSelect={handleDateSelect}
// //       />

// //       {uniqueSoldiers.length > 0 && (
// //         <>
// //           <Text style={styles.header}>חיילים בשיבוץ זה</Text>
// //           <FlatList
// //             data={uniqueSoldiers}
// //             renderItem={renderSoldier}
// //             keyExtractor={(item) => item.id.toString()}
// //             style={styles.soldierList}
// //             contentContainerStyle={{ paddingBottom: 20 }}
// //             showsVerticalScrollIndicator={false}
// //           />
// //         </>
// //       )}

// //       {selectedDate && dailyScheduleInfo ? (
// //         <View style={styles.dayInfo}>
// //           <Text style={styles.dayInfoText}>
// //             📅 <Text style={{ fontWeight: "bold" }}>{dailyScheduleInfo.date}</Text>
// //           </Text>
// //           <Text style={styles.dayInfoText}>
// //             🪖 בבסיס ({dailyScheduleInfo.soldiers_on_base.length}):{" "}
// //             {dailyScheduleInfo.soldiers_on_base.join(", ") || "אין"}
// //           </Text>
// //           <Text style={styles.dayInfoText}>
// //             🏠 בבית ({dailyScheduleInfo.soldiers_at_home.length}):{" "}
// //             {dailyScheduleInfo.soldiers_at_home.join(", ") || "אין"}
// //           </Text>
// //         </View>
// //       ) : selectedDate && !dailyScheduleInfo && !loading ? (
// //         <View style={styles.dayInfo}>
// //             <Text style={styles.dayInfoText}>אין מידע עבור תאריך זה בשיבוץ הנבחר.</Text>
// //         </View>
// //       ) : null}
// //     </ScrollView>
// //   );
// // }

// // const styles = StyleSheet.create({
// //   container: { flex: 1, padding: 20, backgroundColor: "#fff" },
// //   loading: { flex: 1, justifyContent: "center", alignItems: "center" },
// //   errorText: {
// //     fontSize: 18,
// //     color: 'red',
// //     textAlign: 'center',
// //     marginTop: 50,
// //   },
// //   backButton: {
// //     marginTop: 20,
// //     padding: 10,
// //     backgroundColor: '#eee',
// //     borderRadius: 5,
// //     alignSelf: 'center',
// //   },
// //   backButtonText: {
// //     color: '#333',
// //     fontSize: 16,
// //   },
// //   header: {
// //     fontSize: 20,
// //     fontWeight: "bold",
// //     textAlign: "center",
// //     marginBottom: 10,
// //     marginTop: 20,
// //     color: "#333",
// //   },
// //   plusButton: { alignSelf: "center", marginBottom: 20 },
// //   schedulingRunName: {
// //     fontSize: 22,
// //     fontWeight: "bold",
// //     textAlign: "center",
// //     marginBottom: 5,
// //     color: "#6200ee",
// //   },
// //   schedulingRunDateRange: {
// //     fontSize: 16,
// //     textAlign: "center",
// //     marginBottom: 5,
// //     color: "#555",
// //   },
// //   schedulingRunStatus: {
// //     fontSize: 16,
// //     textAlign: "center",
// //     marginBottom: 10,
// //     color: "#555",
// //     fontStyle: 'italic',
// //   },
// //   schedulingRunDetails: {
// //     fontSize: 14,
// //     textAlign: "center",
// //     marginBottom: 15,
// //     color: "#777",
// //   },
// //   paramsContainer: {
// //     backgroundColor: "#f9f9f9",
// //     padding: 15,
// //     borderRadius: 10,
// //     marginBottom: 20,
// //     borderWidth: 1,
// //     borderColor: '#e0e0e0',
// //   },
// //   paramText: {
// //     fontSize: 14,
// //     marginBottom: 5,
// //     color: '#444',
// //   },
// //   dayInfo: {
// //     backgroundColor: "#f0f4f8",
// //     padding: 15,
// //     borderRadius: 10,
// //     marginTop: 20,
// //     shadowColor: "#000",
// //     shadowOffset: { width: 0, height: 2 },
// //     shadowOpacity: 0.1,
// //     shadowRadius: 4,
// //     elevation: 2,
// //   },
// //   dayInfoText: {
// //     fontSize: 15,
// //     color: "#333",
// //     marginVertical: 4,
// //     lineHeight: 24,
// //   },
// //   soldierList: {
// //     maxHeight: 320,
// //   },
// //   card: {
// //     marginVertical: 6,
// //     backgroundColor: "#fff",
// //     borderRadius: 8,
// //     elevation: 3,
// //     shadowColor: "#000",
// //     shadowOffset: { width: 0, height: 1 },
// //     shadowOpacity: 0.2,
// //     shadowRadius: 1.41,
// //   },
// // });