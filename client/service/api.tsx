const getApiBaseUrl = () => {
  if (__DEV__) {
    return 'http://10.0.2.2:8000/api'; // Android emulator
  }
  return process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api';
};

const API_BASE_URL = getApiBaseUrl();

const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Something went wrong');
  }
  return response.json();
};

// --- שירותי חיילים (Soldiers) ---
export const soldierService = {
  /**
   * מקבל את כל החיילים.
   * @returns {Promise<Array>} רשימת חיילים.
   */
  getAllSoldiers: async (): Promise<Array<any>> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/`);
    return handleResponse(response);
  },

  /**
   * מוסיף חייל חדש.
   * @param {object} soldierData - אובייקט עם נתוני החייל (לדוגמה: { name: "שם חייל" }).
   * @returns {Promise<object>} אובייקט החייל שנוצר.
   */
  addSoldier: async (soldierData: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(soldierData),
    });
    return handleResponse(response);
  },

  /**
   * מוסיף אילוץ לחייל ספציפי.
   * @param {number} soldierId - ה-ID של החייל.
   * @param {object} constraintData - אובייקט אילוץ (לדוגמה: { constraint_date: "2025-01-01", description: "חופשה" }).
   * @returns {Promise<object>} אובייקט האילוץ שנוצר.
   */
  addSoldierConstraint: async (soldierId: any, constraintData: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/add_constraint/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(constraintData),
    });
    return handleResponse(response);
  },

  /**
   * מקבל את ספירת החיילים הכוללת.
   * @returns {Promise<object>} אובייקט עם ספירת החיילים (לדוגמה: { total_soldiers: 10 }).
   */
  getSoldierCount: async (): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/count/`);
    return handleResponse(response);
  },

  /**
   * מקבל חייל ספציפי לפי ID.
   * @param {number} soldierId - ה-ID של החייל.
   * @returns {Promise<object>} אובייקט החייל.
   */
  getSoldierById: async (soldierId: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/`);
    return handleResponse(response);
  },

  /**
   * מעדכן חייל קיים.
   * @param {number} soldierId - ה-ID של החייל לעדכון.
   * @param {object} updatedData - הנתונים המעודכנים של החייל.
   * @returns {Promise<object>} אובייקט החייל המעודכן.
   */
  updateSoldier: async (soldierId: any, updatedData: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updatedData),
    });
    return handleResponse(response);
  },

  /**
   * מוחק חייל.
   * @param {number} soldierId - ה-ID של החייל למחיקה.
   * @returns {Promise<void>}
   */
  deleteSoldier: async (soldierId: any): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete soldier');
    }
  },
};

// --- שירותי הרצת שיבוץ (Scheduling Runs) ---
export const schedulingService = {
  /**
   * מקבל את כל הרצות השיבוץ.
   * @returns {Promise<Array>} רשימת הרצות שיבוץ.
   */
  getAllSchedulingRuns: async (): Promise<Array<any>> => {
    const response = await fetch(`${API_BASE_URL}/scheduling-runs/`);
    return handleResponse(response);
  },

  /**
   * מריץ שיבוץ חדש.
   * @param {object} schedulingParams - פרמטרים להרצת השיבוץ (כמו ב-ScheduleCreateSerializer).
   * @returns {Promise<object>} אובייקט הרצת השיבוץ שנוצר.
   */
  runNewScheduling: async (schedulingParams: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/scheduling-runs/run_scheduling_new/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(schedulingParams),
    });
    return handleResponse(response);
  },

  /**
   * מעדכן ומריץ מחדש שיבוץ קיים.
   * @param {object} updateParams - פרמטרים לעדכון הרצת השיבוץ (כמו ב-ScheduleUpdateSerializer).
   * @returns {Promise<object>} אובייקט הרצת השיבוץ המעודכן.
   */
  updateExistingSchedulingRun: async (updateParams: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/scheduling-runs/update_existing_scheduling_run/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateParams),
    });
    return handleResponse(response);
  },

  /**
   * מקבל לוח שיבוץ מפורט עבור הרצת שיבוץ ספציפית.
   * @param {number} runId - ה-ID של הרצת השיבוץ.
   * @returns {Promise<Array>} לוח שיבוץ מפורט לכל יום.
   */
  getDetailedSchedule: async (runId: any): Promise<Array<any>> => {
    const response = await fetch(`${API_BASE_URL}/scheduling-runs/${runId}/detailed_schedule/`);
    return handleResponse(response);
  },

  /**
   * מקבל הרצת שיבוץ ספציפית לפי ID.
   * @param {number} runId - ה-ID של הרצת השיבוץ.
   * @returns {Promise<object>} אובייקט הרצת השיבוץ.
   */
  getSchedulingRunById: async (runId: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/scheduling-runs/${runId}/`);
    return handleResponse(response);
  },
};

// --- שירותי שיבוצים (Assignments) ---
export const assignmentService = {
  /**
   * מקבל את כל השיבוצים.
   * ניתן לסנן לפי פרמטרים.
   * @param {object} [filters={}] - אובייקט אופציונלי של פילטרים (לדוגמה: { soldier: 1, assignment_date: '2025-01-15' }).
   * @returns {Promise<Array>} רשימת שיבוצים.
   */
  getAllAssignments: async (filters: string | Record<string, string> | URLSearchParams | string[][] | undefined): Promise<Array<any>> => {
    const query = new URLSearchParams(filters).toString();
    const url = `${API_BASE_URL}/assignments/${query ? `?${query}` : ''}`;
    const response = await fetch(url);
    return handleResponse(response);
  },

  /**
   * מקבל שיבוץ ספציפי לפי ID.
   * @param {number} assignmentId - ה-ID של השיבוץ.
   * @returns {Promise<object>} אובייקט השיבוץ.
   */
  getAssignmentById: async (assignmentId: any): Promise<object> => {
    const response = await fetch(`${API_BASE_URL}/assignments/${assignmentId}/`);
    return handleResponse(response);
  },
};

// ייצוא פונקציות ספציפיות מתוך השירותים לצורך ייבוא נוח יותר
export const { getSchedulingRunById, getDetailedSchedule } = schedulingService;
export const { getSoldierById } = soldierService;
export const { getAllSoldiers, addSoldier, addSoldierConstraint, getSoldierCount, updateSoldier, deleteSoldier } = soldierService;
export const { runNewScheduling, getAllSchedulingRuns, updateExistingSchedulingRun } = schedulingService;
export const { getAllAssignments, getAssignmentById } = assignmentService;

export const getAllEvents = async () => {
  // מתבסס על הרצות השיבוץ כאירועים
  const data = await schedulingService.getAllSchedulingRuns();
  return data;
};

export const addAssignment = async (assignmentData: any): Promise<object> => {
  const response = await fetch(`${API_BASE_URL}/assignments/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(assignmentData),
  });
  return handleResponse(response);
}

export const updateAssignment = async (assignmentId: number, updatedData: any): Promise<object> => {
  const response = await fetch(`${API_BASE_URL}/assignments/${assignmentId}/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updatedData),
  });
  return handleResponse(response);
}