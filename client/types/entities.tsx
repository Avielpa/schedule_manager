export interface Soldier {
  id: number;
  name: string;

  /**
   * תאריכים שהחייל ביקש לא להיות בבסיס (אילוצים אישיים)
   */
  constraints: string[];

  /**
   * תאריכים בהם החייל נמצא בבסיס לפי השיבוץ
   */
  base_dates: string[];

  /**
   * תאריכים בהם החייל נמצא בבית לפי השיבוץ
   */
  home_dates: string[];
}

export interface Event {
  id: number;
  name: string;
  start_date: string; // תאריך התחלה בפורמט YYYY-MM-DD
  end_date: string;   // תאריך סיום בפורמט YYYY-MM-DD
  max_home_days: number;
  min_soldiers_req: number;
  base_days_diff: number;
  home_days_diff: number;

  /**
   * מערך של חיילים הקשורים לאירוע
   */
  soldier: Soldier[];
}
