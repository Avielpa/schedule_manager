import React, { useEffect, useState } from "react";
import { View, Text, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator, Alert, Button } from "react-native";
import AntDesign from "@expo/vector-icons/AntDesign";
import { useRouter } from "expo-router";
// ודא שהנתיב ל-api.js נכון בהתאם למבנה הפרויקט שלך
import { getAllEvents } from "@/service/api"; 
// ודא שהנתיב ל-entities.ts נכון והגדרת ה-Event תואמת את ה-API שלך
import { Event } from "@/types/entities"; 

export default function Home() {
  const router = useRouter();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(true); // הוספת מצב טעינה
  const [error, setError] = useState<string | null>(null); // הוספת מצב שגיאה

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true); // התחל טעינה
        const data = await getAllEvents();
        if (Array.isArray(data)) {
          setEvents(data);
        } else {
          // מציג אזהרה אם הנתונים אינם מערך
          console.warn("getAllEvents returned data is not an array:", data);
          setEvents([]); // מנקה את הרשימה אם הפורמט שגוי
          setError("פורמט נתונים שגוי מהשרת.");
        }
      } catch (err) {
        console.error("Failed to fetch events:", err);
        setError("אירעה שגיאה בטעינת האירועים. אנא נסה שוב מאוחר יותר.");
        // ניתן להציג הודעה למשתמש
        Alert.alert("שגיאה", "לא ניתן לטעון את האירועים. אנא ודא שהשרת פועל.");
      } finally {
        setLoading(false); // סיים טעינה
      }
    };

    fetchEvents();
  }, []);

  const renderEvent = ({ item }: { item: Event }) => (
    <TouchableOpacity
      style={styles.eventItem}
      onPress={() => {
        if (item.id) {
          router.push(`/event/${item.id}`);
        } else {
          console.warn("Event ID is undefined, cannot navigate.", item);
          Alert.alert("שגיאה", "לא ניתן לנווט לאירוע זה. חסר מזהה.");
        }
      }}
    >
      <Text style={styles.eventName}>{item.name}</Text>
    </TouchableOpacity>
  );

  // תצוגת טעינה
  if (loading) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text>טוען אירועים...</Text>
      </View>
    );
  }

  // תצוגת שגיאה
  if (error) {
    return (
      <View style={styles.centeredContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <Button title="נסה שוב" onPress={() => { /* לוגיקה לטעינה מחדש */ }} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>ניהול אירועים</Text>

      <TouchableOpacity onPress={() => router.push("/eventForm")}>
        <AntDesign style={styles.plusButton} name="pluscircle" size={40} color="blue" />
      </TouchableOpacity>

      {/* הודעה אם אין אירועים */}
      {events.length === 0 && !loading && !error && (
        <Text style={styles.noEventsText}>אין אירועים להצגה. לחץ על הפלוס כדי ליצור אירוע חדש! 🎉</Text>
      )}

      <FlatList
        data={events}
        renderItem={renderEvent}
        // שימוש ב-toString() כדי לוודא שמדובר במחרוזת
        // שימוש ב-?? כדי לספק חלופה (item.name) אם item.id הוא null או undefined
        keyExtractor={(item) => (item.id?.toString() ?? item.name).toString()} 
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    padding: 20, 
    backgroundColor: "#fff" 
  },
  centeredContainer: { // סגנון חדש למרכוז רכיבים כמו טעינה/שגיאה
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: "#fff",
  },
  header: { 
    fontSize: 28, // הגדלתי קצת את הכותרת
    fontWeight: "bold", 
    textAlign: "center", 
    marginBottom: 20, // הגדלתי מרווח
    color: '#333',
  },
  plusButton: { 
    alignSelf: "center", 
    marginBottom: 25, // הגדלתי מרווח
    color: '#007bff', // צבע כפתור פלוס
  },
  listContainer: { 
    paddingBottom: 20, 
  },
  eventItem: {
    padding: 15,
    backgroundColor: "#e0f7fa", // צבע רקע עדין יותר
    borderRadius: 10, // פינות מעוגלות יותר
    marginBottom: 12, // הגדלתי מרווח בין פריטים
    shadowColor: "#000", // הוספת צל
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  eventName: { 
    fontSize: 20, // הגדלתי את גודל הטקסט
    fontWeight: "700", // משקל כבד יותר
    color: 'black',
  },
  noEventsText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#666',
    fontStyle: 'italic',
  },
  errorText: {
    color: 'red',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 10,
  }
});














// import React, { useEffect, useState } from "react";
// import { View, Text, TouchableOpacity, FlatList, StyleSheet } from "react-native";
// import AntDesign from "@expo/vector-icons/AntDesign";
// import { useRouter } from "expo-router";
// import { getAllEvents } from "@/service/api";
// import { Event } from "@/types/entities";

// export default function Home() {
//   const router = useRouter();
//   const [events, setEvents] = useState<Event[]>([]);

//   useEffect(() => {
//     const fetchEvents = async () => {
//       try {
//         const data = await getAllEvents();
//         if (Array.isArray(data)) {
//           setEvents(data);
//         } else {
//           console.warn("getAllEvents returned data is not an array", data);
//           setEvents([]);
//         }
//       } catch (error) {
//         console.error("Failed to fetch events:", error);
//       }
//     };

//     fetchEvents();
//   }, []);

//   const renderEvent = ({ item }: { item: Event }) => (
//     <TouchableOpacity
//       style={styles.eventItem}
//       onPress={() => {
//         // בהתאם ל-expo-router נשתמש בrouter.push עם path string כולל הפרמטרים
//         router.push(`/event/${item.id}`);
//       }}
//     >
//       <Text style={styles.eventName}>{item.name}</Text>
//     </TouchableOpacity>
//   );

//   return (
//     <View style={styles.container}>
//       <Text style={styles.header}>Create Event</Text>

//       <TouchableOpacity onPress={() => router.push("/eventForm")}>
//         <AntDesign style={styles.plusButton} name="pluscircle" size={40} color="black" />
//       </TouchableOpacity>

//       <FlatList
//         data={events}
//         renderItem={renderEvent}
//         keyExtractor={(item) => item.id.toString() ?? item.name}
//         contentContainerStyle={styles.listContainer}
//         showsVerticalScrollIndicator={false}
//       />
//     </View>
//   );
// }

// const styles = StyleSheet.create({
//   container: { flex: 1, padding: 20, backgroundColor: "#fff" },
//   header: { fontSize: 24, fontWeight: "bold", textAlign: "center", marginBottom: 10 },
//   plusButton: { alignSelf: "center", marginBottom: 20 },
//   listContainer: { paddingBottom: 20 },
//   eventItem: {
//     padding: 15,
//     backgroundColor: "#f1f1f1",
//     borderRadius: 8,
//     marginBottom: 10,
//   },
//   eventName: { fontSize: 18, fontWeight: "600" },
// });




















// // import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
// // import AntDesign from '@expo/vector-icons/AntDesign';
// // import { useRouter } from 'expo-router';
// // import { useEffect, useState } from 'react';
// // import { getAllEvents } from '@/service/api'; 
// // import { Event } from '@/types/entities';

// // export default function Home() {
// //   const router = useRouter();
// //   const [events, setEvents] = useState<Event[]>([]);

// //   useEffect(() => {
// //     const fetchEvents = async () => {
// //       const data = await getAllEvents();
// //       setEvents(data);
// //     };

// //     fetchEvents();
// //   }, []);

// //   const renderEvent = ({ item }: { item: Event }) => (
// //     <TouchableOpacity
// //       style={styles.eventItem}
// //       onPress={() => router.push({        
// //         pathname: "/event/[id]",
// //         params:{id:item._id},}
// //       )}
// //     >
// //       <Text style={styles.eventName}>{item.name}</Text>
// //     </TouchableOpacity>
// //   );

// //   return (
// //     <View style={styles.container}>
// //       <Text style={styles.header}>Create Event</Text>

// //       <TouchableOpacity onPress={() => router.push('/eventForm')}>
// //         <AntDesign style={styles.plusButton} name="pluscircle" size={40} color="black" />
// //       </TouchableOpacity>

// //       <FlatList
// //         data={events}
// //         renderItem={renderEvent}
// //         keyExtractor={(item) => item._id?.toString()}
// //         contentContainerStyle={styles.listContainer}
// //       />
// //     </View>
// //   );
// // }


// // const styles = StyleSheet.create({
// //   container: { flex: 1, padding: 20 },
// //   header: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 10 },
// //   plusButton: { alignSelf: 'center', marginBottom: 20 },
// //   listContainer: { paddingBottom: 20 },
// //   eventItem: {
// //     padding: 15,
// //     backgroundColor: '#f1f1f1',
// //     borderRadius: 8,
// //     marginBottom: 10,
// //   },
// //   eventName: { fontSize: 18, fontWeight: '600' },
// // });

