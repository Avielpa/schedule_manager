import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, Switch } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { updateAssignment } from '@/service/api';
import { format } from 'date-fns';

export default function EditAssignmentScreen() {
  const params = useLocalSearchParams();
  const { assignmentId, soldierId, soldierName, assignmentDate: initialAssignmentDate, isOnBase: initialIsOnBase, schedulingRunId } = params;

  const [isOnBase, setIsOnBase] = useState(initialIsOnBase === 'true'); // המרה מסטרינג לבוליאן
  const [loading, setLoading] = useState(false);
  const [assignmentDate, setAssignmentDate] = useState<string>(initialAssignmentDate as string || '');

  useEffect(() => {
    if (!assignmentId || !soldierId || !schedulingRunId) {
      Alert.alert("שגיאה", "פרטי שיבוץ, חייל או ריצת שיבוץ חסרים.");
      router.back();
    }
  }, [assignmentId, soldierId, schedulingRunId]);

  const handleUpdateAssignment = async () => {
    if (!assignmentId || !soldierId || !schedulingRunId || !assignmentDate) {
      Alert.alert("שגיאה", "אנא מלא את כל השדות הנדרשים.");
      return;
    }

    setLoading(true);
    try {
      // כאן אנו מניחים שלשירות ה-API יש פונקציה 'updateAssignment'
      // שתקבל את ה-ID של השיבוץ ואת הנתונים המעודכנים.
      const updatedAssignment = await updateAssignment(Number(assignmentId), {
        soldier: Number(soldierId),
        assignment_date: assignmentDate,
        is_on_base: isOnBase,
        scheduling_run: Number(schedulingRunId),
      });
      Alert.alert("הצלחה", `שיבוץ עודכן בהצלחה ל${soldierName}`);
      router.back(); // חזור למסך הקודם
    } catch (error:any) {
      console.error("שגיאה בעדכון שיבוץ:", error);
      Alert.alert("שגיאה", `נכשל לעדכן שיבוץ: ${error.message || 'נסה שוב.'}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <ActivityIndicator size="large" color="#6200ee" style={styles.loading} />;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>עריכת שיבוץ קיים</Text>
      <Text style={styles.subtitle}>עבור: {soldierName}</Text>
      <Text style={styles.subtitle}>תאריך: {format(new Date(assignmentDate), 'dd/MM/yyyy')}</Text>


      <View style={styles.inputGroup}>
        <Text style={styles.label}>תאריך שיבוץ:</Text>
        <TextInput
          style={styles.input}
          value={assignmentDate}
          onChangeText={setAssignmentDate}
          placeholder="YYYY-MM-DD"
          keyboardType="numeric"
        />
        <Text style={styles.helpText}>פורמט: שנה-חודש-יום (לדוגמה: 2025-07-20)</Text>
      </View>

      <View style={styles.switchContainer}>
        <Text style={styles.label}>האם החייל בבסיס?</Text>
        <Switch
          onValueChange={setIsOnBase}
          value={isOnBase}
          trackColor={{ false: "#767577", true: "#81b0ff" }}
          thumbColor={isOnBase ? "#f5dd4b" : "#f4f3f4"}
        />
        <Text style={styles.switchText}>{isOnBase ? "בבסיס" : "בבית"}</Text>
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={handleUpdateAssignment}
        disabled={loading}
      >
        <Text style={styles.buttonText}>עדכן שיבוץ</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.cancelButton]}
        onPress={() => router.back()}
      >
        <Text style={styles.buttonText}>ביטול</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f8f8f8',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#3f51b5',
  },
  subtitle: {
    fontSize: 18,
    color: '#555',
    marginBottom: 10,
  },
  inputGroup: {
    width: '90%',
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    marginBottom: 8,
    color: '#444',
    fontWeight: '600',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  helpText: {
    fontSize: 12,
    color: '#888',
    marginTop: 5,
    textAlign: 'left',
  },
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 30,
    backgroundColor: '#e3f2fd',
    padding: 15,
    borderRadius: 10,
    width: '90%',
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  switchText: {
    fontSize: 16,
    marginLeft: 10,
    color: '#444',
  },
  button: {
    backgroundColor: '#6200ee',
    padding: 15,
    borderRadius: 10,
    width: '90%',
    alignItems: 'center',
    marginVertical: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 3,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    backgroundColor: '#d32f2f',
  },
});