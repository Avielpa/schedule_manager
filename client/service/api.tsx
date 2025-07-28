// src/services/apiService.js

const API_BASE_URL = 'http://10.0.2.2:8000/api'; // שנה את ה-IP לכתובת השרת שלך!

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
export const { getSoldierById } = soldierService; // אם תצטרך לשלוף פרטי חייל מלאים
export const { getAllSoldiers, addSoldier, addSoldierConstraint, getSoldierCount, updateSoldier, deleteSoldier } = soldierService;
export const { runNewScheduling, getAllSchedulingRuns, updateExistingSchedulingRun } = schedulingService;
export const { getAllAssignments, getAssignmentById } = assignmentService;

export const getAllEvents = async () => {
  // יש צורך לשנות את זה לנקודת הקצה שבאמת מחזירה אירועים
  // בהתבסס על ה-views.py שלך, אולי תצטרך ליצור viewset חדש לאירועים,
  // או להשתמש ב-schedulingService.getAllSchedulingRuns() אם זה מה שאתה מתכוון כ"אירועים"
  // לדוגמה, אם כל הרצת שיבוץ היא אירוע:
  const data = await schedulingService.getAllSchedulingRuns();
  return data; // ודא שזה מחזיר מערך של אובייקטים עם 'id' ו-'name'
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
    method: 'PUT', // או PATCH, תלוי ב-API שלך
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updatedData),
  });
  return handleResponse(response);
}



























// // src/services/apiService.js

// const API_BASE_URL = 'http://10.0.2.2:8000/api'; // שנה את ה-IP לכתובת השרת שלך!

// const handleResponse = async (response: Response) => {
//   if (!response.ok) {
//     const errorData = await response.json();
//     throw new Error(errorData.detail || 'Something went wrong');
//   }
//   return response.json();
// };

// // --- שירותי חיילים (Soldiers) ---
// export const soldierService = {
//   /**
//    * מקבל את כל החיילים.
//    * @returns {Promise<Array>} רשימת חיילים.
//    */
//   getAllSoldiers: async (): Promise<Array<any>> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/`);
//     return handleResponse(response);
//   },

//   /**
//    * מוסיף חייל חדש.
//    * @param {object} soldierData - אובייקט עם נתוני החייל (לדוגמה: { name: "שם חייל" }).
//    * @returns {Promise<object>} אובייקט החייל שנוצר.
//    */
//   addSoldier: async (soldierData: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(soldierData),
//     });
//     return handleResponse(response);
//   },

//   /**
//    * מוסיף אילוץ לחייל ספציפי.
//    * @param {number} soldierId - ה-ID של החייל.
//    * @param {object} constraintData - אובייקט אילוץ (לדוגמה: { constraint_date: "2025-01-01", description: "חופשה" }).
//    * @returns {Promise<object>} אובייקט האילוץ שנוצר.
//    */
//   addSoldierConstraint: async (soldierId: any, constraintData: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/add-constraint/`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(constraintData),
//     });
//     return handleResponse(response);
//   },

//   /**
//    * מקבל את ספירת החיילים הכוללת.
//    * @returns {Promise<object>} אובייקט עם ספירת החיילים (לדוגמה: { total_soldiers: 10 }).
//    */
//   getSoldierCount: async (): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/count/`);
//     return handleResponse(response);
//   },

//   /**
//    * מקבל חייל ספציפי לפי ID.
//    * @param {number} soldierId - ה-ID של החייל.
//    * @returns {Promise<object>} אובייקט החייל.
//    */
//   getSoldierById: async (soldierId: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/`);
//     return handleResponse(response);
//   },

//   /**
//    * מעדכן חייל קיים.
//    * @param {number} soldierId - ה-ID של החייל לעדכון.
//    * @param {object} updatedData - הנתונים המעודכנים של החייל.
//    * @returns {Promise<object>} אובייקט החייל המעודכן.
//    */
//   updateSoldier: async (soldierId: any, updatedData: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/`, {
//       method: 'PUT',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(updatedData),
//     });
//     return handleResponse(response);
//   },

//   /**
//    * מוחק חייל.
//    * @param {number} soldierId - ה-ID של החייל למחיקה.
//    * @returns {Promise<void>}
//    */
//   deleteSoldier: async (soldierId: any): Promise<void> => {
//     const response = await fetch(`${API_BASE_URL}/soldiers/${soldierId}/`, {
//       method: 'DELETE',
//     });
//     if (!response.ok) {
//       const errorData = await response.json();
//       throw new Error(errorData.detail || 'Failed to delete soldier');
//     }
//   },
// };

// // --- שירותי הרצת שיבוץ (Scheduling Runs) ---
// export const schedulingService = {
//   /**
//    * מקבל את כל הרצות השיבוץ.
//    * @returns {Promise<Array>} רשימת הרצות שיבוץ.
//    */
//   getAllSchedulingRuns: async (): Promise<Array<any>> => {
//     const response = await fetch(`${API_BASE_URL}/scheduling-runs/`);
//     return handleResponse(response);
//   },

//   /**
//    * מריץ שיבוץ חדש.
//    * @param {object} schedulingParams - פרמטרים להרצת השיבוץ (כמו ב-ScheduleCreateSerializer).
//    * @returns {Promise<object>} אובייקט הרצת השיבוץ שנוצר.
//    */
//   runNewScheduling: async (schedulingParams: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/scheduling-runs/run_scheduling_new/`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(schedulingParams),
//     });
//     return handleResponse(response);
//   },

//   /**
//    * מעדכן ומריץ מחדש שיבוץ קיים.
//    * @param {object} updateParams - פרמטרים לעדכון הרצת השיבוץ (כמו ב-ScheduleUpdateSerializer).
//    * @returns {Promise<object>} אובייקט הרצת השיבוץ המעודכן.
//    */
//   updateExistingSchedulingRun: async (updateParams: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/scheduling-runs/update_existing_scheduling_run/`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(updateParams),
//     });
//     return handleResponse(response);
//   },

//   /**
//    * מקבל לוח שיבוץ מפורט עבור הרצת שיבוץ ספציפית.
//    * @param {number} runId - ה-ID של הרצת השיבוץ.
//    * @returns {Promise<Array>} לוח שיבוץ מפורט לכל יום.
//    */
//   getDetailedSchedule: async (runId: any): Promise<Array<any>> => {
//     const response = await fetch(`${API_BASE_URL}/scheduling-runs/${runId}/detailed_schedule/`);
//     return handleResponse(response);
//   },

//   /**
//    * מקבל הרצת שיבוץ ספציפית לפי ID.
//    * @param {number} runId - ה-ID של הרצת השיבוץ.
//    * @returns {Promise<object>} אובייקט הרצת השיבוץ.
//    */
//   getSchedulingRunById: async (runId: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/scheduling-runs/${runId}/`);
//     return handleResponse(response);
//   },
// };

// // --- שירותי שיבוצים (Assignments) ---
// export const assignmentService = {
//   /**
//    * מקבל את כל השיבוצים.
//    * ניתן לסנן לפי פרמטרים.
//    * @param {object} [filters={}] - אובייקט אופציונלי של פילטרים (לדוגמה: { soldier: 1, assignment_date: '2025-01-15' }).
//    * @returns {Promise<Array>} רשימת שיבוצים.
//    */
//   getAllAssignments: async (filters: string | Record<string, string> | URLSearchParams | string[][] | undefined): Promise<Array<any>> => {
//     const query = new URLSearchParams(filters).toString();
//     const url = `${API_BASE_URL}/assignments/${query ? `?${query}` : ''}`;
//     const response = await fetch(url);
//     return handleResponse(response);
//   },

//   /**
//    * מקבל שיבוץ ספציפי לפי ID.
//    * @param {number} assignmentId - ה-ID של השיבוץ.
//    * @returns {Promise<object>} אובייקט השיבוץ.
//    */
//   getAssignmentById: async (assignmentId: any): Promise<object> => {
//     const response = await fetch(`${API_BASE_URL}/assignments/${assignmentId}/`);
//     return handleResponse(response);
//   },
// };


// export const getAllEvents = async () => {
//   // יש צורך לשנות את זה לנקודת הקצה שבאמת מחזירה אירועים
//   // בהתבסס על ה-views.py שלך, אולי תצטרך ליצור viewset חדש לאירועים,
//   // או להשתמש ב-schedulingService.getAllSchedulingRuns() אם זה מה שאתה מתכוון כ"אירועים"
//   // לדוגמה, אם כל הרצת שיבוץ היא אירוע:
//   const data = await schedulingService.getAllSchedulingRuns();
//   return data; // ודא שזה מחזיר מערך של אובייקטים עם 'id' ו-'name'
// };



























// // api.tsx
// import axios from 'axios';

// // ----------------------------------------------------------------------
// // 1. הגדרות טיפוסים (Interfaces/Types)
// // ----------------------------------------------------------------------

// /**
//  * ממשק עבור אובייקט Event (אירוע) כפי שמתקבל מה-API.
//  * שים לב: תאריכים מועברים כמחרוזות בפורמט YYYY-MM-DD.
//  */
// export interface Event {
//   id: number;
//   name: string;
//   start_date: string; // YYYY-MM-DD
//   end_date: string;   // YYYY-MM-DD
//   default_base_days_target: number;
//   default_home_days_target: number;
//   max_consecutive_base_days: number;
//   max_consecutive_home_days: number;
//   min_base_block_days: number;
//   min_required_soldiers_per_day: number;
//   max_total_home_days: number | null;
// }

// /**
//  * ממשק עבור אובייקט Soldier (חייל) כפי שמתקבל מה-API.
//  * שים לב: constraints, base_dates, home_dates מועברים כמערכי מחרוזות תאריכים.
//  */
// export interface Soldier {
//   id: number;
//   name: string;
//   event: number; // ID של האירוע אליו החייל משויך
//   constraints: string[]; // מערך של תאריכים בפורמט YYYY-MM-DD שהחייל לא זמין בהם
//   base_dates: string[]; // מערך של תאריכים בפורמט YYYY-MM-DD שהחייל משובץ בהם לבסיס (נקבע ע"י האלגוריתם)
//   home_dates: string[]; // מערך של תאריכים בפורמט YYYY-MM-DD שהחייל משובץ בהם לבית (נקבע ע"י האלגוריתם)
// }

// /**
//  * ממשק עבור נתוני הקלט הנדרשים להפעלת אלגוריתם השיבוץ.
//  * אלו הפרמטרים שנשלחים ב-POST request ל-run-smart-schedule.
//  */
// export interface RunScheduleParams {
//   default_base_days_target: number;
//   default_home_days_target: number;
//   max_consecutive_base_days: number;
//   max_consecutive_home_days: number;
//   min_base_block_days: number;
//   min_required_soldiers_per_day: number;
//   max_total_home_days: number | null;
// }

// /**
//  * ממשק עבור התגובה הצפויה מהשרת לאחר הפעלת אלגוריתם השיבוץ.
//  */
// export interface RunScheduleResponse {
//   status: 'success' | 'error';
//   message: string;
//   schedule: { [date: string]: string[] }; // מפה של תאריך (YYYY-MM-DD) לרשימת שמות חיילים
//   soldiers_details: Soldier[]; // רשימת אובייקטי החיילים המעודכנים
// }

// /**
//  * ממשק עבור תגובת שגיאה כללית מה-API.
//  */
// export interface ErrorResponse {
//   status: 'error';
//   message: string;
//   // ניתן להוסיף שדות נוספים לשגיאות, לדוגמה:
//   // details?: any;
// }

// // ----------------------------------------------------------------------
// // 2. הגדרת בסיס ל-Axios
// // ----------------------------------------------------------------------

// // הגדר את ה-URL הבסיסי של ה-API שלך.
// // לדוגמה: 'http://localhost:8000/api/' אם השרת שלך רץ על פורט 8000
// // וקובץ urls.py הראשי שלך מכיל path('api/', include('your_app_name.urls'))
// const API_BASE_URL = 'http://localhost:8000/api/'; // שנה את זה לפי ההגדרה שלך!

// const api = axios.create({
//   baseURL: API_BASE_URL,
//   headers: {
//     'Content-Type': 'application/json',
//   },
// });

// // ----------------------------------------------------------------------
// // 3. פונקציות API עבור Event (אירועים)
// // ----------------------------------------------------------------------

// export const eventsApi = {
//   /**
//    * קבלת רשימת כל האירועים.
//    * GET /api/events/
//    */
//   getAllEvents: async (): Promise<Event[]> => {
//     try {
//       const response = await api.get<Event[]>('events/');
//       return response.data;
//     } catch (error) {
//       console.error('Error fetching events:', error);
//       throw error; // זרוק את השגיאה לטיפול בקומפוננטה שקוראת
//     }
//   },

//   /**
//    * קבלת אירוע ספציפי לפי ID.
//    * GET /api/events/{id}/
//    */
//   getEventById: async (id: number): Promise<Event> => {
//     try {
//       const response = await api.get<Event>(`events/${id}/`);
//       return response.data;
//     } catch (error) {
//       console.error(`Error fetching event with ID ${id}:`, error);
//       throw error;
//     }
//   },

//   /**
//    * יצירת אירוע חדש.
//    * POST /api/events/
//    */
//   createEvent: async (eventData: Omit<Event, 'id'>): Promise<Event> => {
//     try {
//       const response = await api.post<Event>('events/', eventData);
//       return response.data;
//     } catch (error) {
//       console.error('Error creating event:', error);
//       throw error;
//     }
//   },

//   /**
//    * עדכון אירוע קיים (עדכון מלא).
//    * PUT /api/events/{id}/
//    */
//   updateEvent: async (id: number, eventData: Partial<Event>): Promise<Event> => {
//     try {
//       const response = await api.put<Event>(`events/${id}/`, eventData);
//       return response.data;
//     } catch (error) {
//       console.error(`Error updating event with ID ${id}:`, error);
//       throw error;
//     }
//   },

//   /**
//    * עדכון חלקי של אירוע קיים.
//    * PATCH /api/events/{id}/
//    */
//   patchEvent: async (id: number, eventData: Partial<Event>): Promise<Event> => {
//     try {
//       const response = await api.patch<Event>(`events/${id}/`, eventData);
//       return response.data;
//     } catch (error) {
//       console.error(`Error patching event with ID ${id}:`, error);
//       throw error;
//     }
//   },

//   /**
//    * מחיקת אירוע.
//    * DELETE /api/events/{id}/
//    */
//   deleteEvent: async (id: number): Promise<void> => {
//     try {
//       await api.delete(`events/${id}/`);
//     } catch (error) {
//       console.error(`Error deleting event with ID ${id}:`, error);
//       throw error;
//     }
//   },
// };

// // ----------------------------------------------------------------------
// // 4. פונקציות API עבור Soldier (חיילים)
// // ----------------------------------------------------------------------

// export const soldiersApi = {
//   /**
//    * קבלת רשימת כל החיילים.
//    * GET /api/soldiers/
//    */
//   getAllSoldiers: async (): Promise<Soldier[]> => {
//     try {
//       const response = await api.get<Soldier[]>('soldiers/');
//       return response.data;
//     } catch (error) {
//       console.error('Error fetching soldiers:', error);
//       throw error;
//     }
//   },

//   /**
//    * קבלת חייל ספציפי לפי ID.
//    * GET /api/soldiers/{id}/
//    */
//   getSoldierById: async (id: number): Promise<Soldier> => {
//     try {
//       const response = await api.get<Soldier>(`soldiers/${id}/`);
//       return response.data;
//     } catch (error) {
//       console.error(`Error fetching soldier with ID ${id}:`, error);
//       throw error;
//     }
//   },

//   /**
//    * יצירת חייל חדש.
//    * POST /api/soldiers/
//    *
//    * הערה: בעת יצירת חייל, יש לכלול את ה-ID של האירוע אליו הוא משויך.
//    * לדוגמה: { name: "חייל חדש", event: 1, constraints: ["2025-07-20"] }
//    */
//   createSoldier: async (soldierData: Omit<Soldier, 'id' | 'base_dates' | 'home_dates'>): Promise<Soldier> => {
//     try {
//       const response = await api.post<Soldier>('soldiers/', soldierData);
//       return response.data;
//     } catch (error) {
//       console.error('Error creating soldier:', error);
//       throw error;
//     }
//   },

//   /**
//    * עדכון חייל קיים (עדכון מלא).
//    * PUT /api/soldiers/{id}/
//    */
//   updateSoldier: async (id: number, soldierData: Partial<Soldier>): Promise<Soldier> => {
//     try {
//       const response = await api.put<Soldier>(`soldiers/${id}/`, soldierData);
//       return response.data;
//     } catch (error) {
//       console.error(`Error updating soldier with ID ${id}:`, error);
//       throw error;
//     }
//   },

//   /**
//    * עדכון חלקי של חייל קיים.
//    * PATCH /api/soldiers/{id}/
//    */
//   patchSoldier: async (id: number, soldierData: Partial<Soldier>): Promise<Soldier> => {
//     try {
//       const response = await api.patch<Soldier>(`soldiers/${id}/`, soldierData);
//       return response.data;
//     } catch (error) {
//       console.error(`Error patching soldier with ID ${id}:`, error);
//       throw error;
//     }
//   },

//   /**
//    * מחיקת חייל.
//    * DELETE /api/soldiers/{id}/
//    */
//   deleteSoldier: async (id: number): Promise<void> => {
//     try {
//       await api.delete(`soldiers/${id}/`);
//     } catch (error) {
//       console.error(`Error deleting soldier with ID ${id}:`, error);
//       throw error;
//     }
//   },
// };

// // ----------------------------------------------------------------------
// // 5. פונקציות API עבור אלגוריתם השיבוץ
// // ----------------------------------------------------------------------

// export const scheduleApi = {
//   /**
//    * מפעיל את אלגוריתם השיבוץ החכם עבור אירוע ספציפי.
//    * POST /api/events/{event_id}/run-smart-schedule/
//    */
//   runSmartSchedule: async (event_id: number, params: RunScheduleParams): Promise<RunScheduleResponse> => {
//     try {
//       const response = await api.post<RunScheduleResponse>(`events/${event_id}/run-smart-schedule/`, params);
//       return response.data;
//     } catch (error) {
//       console.error(`Error running smart schedule for event ID ${event_id}:`, error);
//       // ניתן לטפל בשגיאות ספציפיות יותר כאן, לדוגמה:
//       // if (axios.isAxiosError(error) && error.response) {
//       //   console.error("Server error details:", error.response.data);
//       // }
//       throw error;
//     }
//   },
// };

// // ----------------------------------------------------------------------
// // 6. ייצוא כללי לגישה נוחה
// // ----------------------------------------------------------------------

// const apiService = {
//   events: eventsApi,
//   soldiers: soldiersApi,
//   schedule: scheduleApi,
// };

// export default apiService;