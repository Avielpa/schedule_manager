# algorithms/soldier.py
from datetime import date, timedelta
from typing import List, Optional, Set, Dict

class Soldier:
    """
    Improved class for representing a soldier in the scheduling system.
    Includes automatic analysis of constraints and dynamic parameter setting.
    Adapted for full compatibility with Django views and the scheduling algorithm.
    """
    
    def __init__(self, 
                 id: str, 
                 name: str, 
                 unavailable_days: List[str], 
                 is_exceptional_output: bool = False,
                 is_weekend_only_soldier_flag: bool = False,
                 color: Optional[str] = None):
        
        # Basic information with protections
        self.id = self._validate_id(id)
        self.name = self._validate_and_clean_name(name)
        self.color = color
        
        # Convert dates to date objects with protections
        self.raw_constraints = set()
        self._process_unavailable_days(unavailable_days)

        # Boolean inputs from the user
        self.is_exceptional_output = bool(is_exceptional_output)
        self.is_weekend_only_soldier_flag = bool(is_weekend_only_soldier_flag)

        # Attributes that will be set dynamically (overrides)
        self.max_base_days_override: Optional[int] = None
        self.max_home_days_override: Optional[int] = None
        self.default_home_days_target_override: Optional[int] = None
        
        # Indicators for changing weight in the objective function
        self.reduce_home_balance_penalty_weight: bool = False
        self.reduce_weekend_fairness_weight: bool = False
        
        # Information derived from the scheduling solution (initialized later)
        self.base_dates: List[date] = []
        self.home_dates: List[date] = []
        
        # Additional information for analysis
        self._constraint_analysis: Dict = {}
        self._analysis_completed: bool = False
        
        # Initial data validation checks
        self._validate_soldier_data()

    def _validate_id(self, id_value: str) -> str:
        """Ensures the ID is valid"""
        if not id_value:
            raise ValueError("Soldier ID cannot be empty")
        
        # Clean the ID
        cleaned_id = str(id_value).strip()
        if not cleaned_id:
            raise ValueError("Soldier ID cannot be empty after cleaning")
        
        return cleaned_id

    def _validate_and_clean_name(self, name: str) -> str:
        """Validates and cleans the soldier's name"""
        if not name:
            print(f"⚠️ Warning: Soldier with ID {getattr(self, 'id', 'unknown')} has no name - adding default name")
            return f"Soldier_{getattr(self, 'id', 'unknown')}"
        
        # Clean the name
        cleaned_name = str(name).strip()
        
        if not cleaned_name:
            print(f"⚠️ Warning: Soldier with ID {getattr(self, 'id', 'unknown')} has an empty name - adding default name")
            return f"Soldier_{getattr(self, 'id', 'unknown')}"
        
        # Remove special characters that might cause issues
        # Keep only letters (including Hebrew), numbers, spaces, and hyphens
        import re
        cleaned_name = re.sub(r'[^\w\s\u0590-\u05FF\-]', '', cleaned_name)
        cleaned_name = cleaned_name.strip()
        
        if not cleaned_name:
            print(f"⚠️ Warning: Soldier name was removed during cleaning - adding default name")
            return f"Soldier_{getattr(self, 'id', 'unknown')}"
        
        # Limit name length
        if len(cleaned_name) > 50:
            cleaned_name = cleaned_name[:50]
            print(f"⚠️ Warning: Soldier name truncated to 50 characters")
        
        return cleaned_name

    def _process_unavailable_days(self, unavailable_days: List[str]) -> None:
        """Processes the list of unavailable days with protections"""
        if not unavailable_days:
            return
        
        valid_constraints = 0
        invalid_constraints = 0
        
        for day_str in unavailable_days:
            try:
                if day_str and str(day_str).strip():  # Ensure it's not empty
                    constraint_date = date.fromisoformat(str(day_str).strip())
                    self.raw_constraints.add(constraint_date)
                    valid_constraints += 1
                else:
                    invalid_constraints += 1
            except (ValueError, TypeError) as e:
                print(f"⚠️ Warning: Invalid date for {self.name}: {day_str} - {e}")
                invalid_constraints += 1
        
        if invalid_constraints > 0:
            print(f"⚠️ Soldier {self.name}: {valid_constraints} valid constraints, {invalid_constraints} invalid constraints")

    def _validate_soldier_data(self):
        """Data validation checks for the soldier"""
        if not self.name or not self.name.strip():
            raise ValueError(f"Soldier name cannot be empty")
            
        if not self.id or not self.id.strip():
            raise ValueError(f"Soldier ID cannot be empty")

        # Check flag consistency
        if self.is_weekend_only_soldier_flag and not self.is_exceptional_output:
            print(f"ℹ️ Note: {self.name} is set as a weekend-only soldier but not as exceptional output")

        # Check constraint validity
        if not isinstance(self.raw_constraints, set):
            print(f"⚠️ Warning: raw_constraints is not of type set for {self.name} - converting to set")
            self.raw_constraints = set(self.raw_constraints) if self.raw_constraints else set()

    def analyze_soldier_specific_parameters(self, 
                                            global_max_consecutive_home_days: int,
                                            global_default_home_days_target: int,
                                            calendar_length: int):
        """
        Analyzes the soldier's constraints and sets specific parameters for them.
        Based on flags entered by the user and global parameters.
        """
        if self._analysis_completed:
            return
            
        print(f"🔍 Analyzing specific parameters for {self.name}...")
        
        # Reset parameters before new analysis
        self._reset_overrides()
        
        # Basic constraint analysis
        self._analyze_constraints_patterns()
        
        # Handle exceptional outputs
        if self.is_exceptional_output:
            self._handle_exceptional_output_analysis(
                global_max_consecutive_home_days, 
                global_default_home_days_target, 
                calendar_length
            )
        
        # Handle weekend-only soldiers
        if self.is_weekend_only_soldier_flag:
            self._handle_weekend_only_analysis()
            
        # Report determined changes
        self._report_analysis_results()
        
        self._analysis_completed = True

    def _reset_overrides(self):
        """Resets all overrides before a new analysis"""
        self.max_base_days_override = None
        self.max_home_days_override = None
        self.default_home_days_target_override = None
        self.reduce_home_balance_penalty_weight = False
        self.reduce_weekend_fairness_weight = False

    def _analyze_constraints_patterns(self):
        """Analyzes the soldier's constraint patterns"""
        if not self.raw_constraints:
            self._constraint_analysis = {
                'total_constrained_days': 0,
                'longest_consecutive_block': 0,
                'number_of_blocks': 0,
                'weekend_constraints': 0,
                'scattered_constraints': 0,
                'constraint_blocks': []
            }
            return

        try:
            sorted_constraints = sorted(list(self.raw_constraints))
            
            # Calculate consecutive blocks
            blocks = []
            if sorted_constraints:
                current_block_start = sorted_constraints[0]
                current_block_length = 1
                
                for i in range(1, len(sorted_constraints)):
                    if sorted_constraints[i] == sorted_constraints[i-1] + timedelta(days=1):
                        current_block_length += 1
                    else:
                        blocks.append((current_block_start, current_block_length))
                        current_block_start = sorted_constraints[i]
                        current_block_length = 1
                
                blocks.append((current_block_start, current_block_length))
            
            # Weekend analysis
            weekend_constraints = sum(1 for d in self.raw_constraints if d.weekday() == 5)
            
            # Dispersion analysis
            scattered_constraints = len([block for block in blocks if block[1] == 1])
            
            self._constraint_analysis = {
                'total_constrained_days': len(self.raw_constraints),
                'longest_consecutive_block': max(block[1] for block in blocks) if blocks else 0,
                'number_of_blocks': len(blocks),
                'weekend_constraints': weekend_constraints,
                'scattered_constraints': scattered_constraints,
                'constraint_blocks': blocks
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing constraints for {self.name}: {e}")
            self._constraint_analysis = {
                'total_constrained_days': len(self.raw_constraints),
                'longest_consecutive_block': 0,
                'number_of_blocks': 0,
                'weekend_constraints': 0,
                'scattered_constraints': 0,
                'constraint_blocks': []
            }

    def _handle_exceptional_output_analysis(self, 
                                            global_max_consecutive_home_days: int,
                                            global_default_home_days_target: int,
                                            calendar_length: int):
        """
        Handles the analysis of exceptional outputs (when is_exceptional_output = True).
        Determines if the soldier is exceptional in terms of consecutive home days or total home days.
        """
        print(f"   🚨 Handling exceptional outputs for {self.name}")
        
        longest_block = self._constraint_analysis['longest_consecutive_block']
        total_days = self._constraint_analysis['total_constrained_days']
        
        # 1. Exceptional consecutive home days
        if longest_block > global_max_consecutive_home_days:
            self.max_home_days_override = longest_block + 2  # Safety margin
            self.reduce_home_balance_penalty_weight = True
            print(f"      📅 Setting override for consecutive home days: {self.max_home_days_override}")

        # 2. Exceptional total home days
        if total_days > global_default_home_days_target:
            # Add a safety margin of 20% or 3 days (whichever is higher)
            safety_margin = max(3, int(total_days * 0.2))
            self.default_home_days_target_override = total_days + safety_margin
            self.reduce_home_balance_penalty_weight = True
            print(f"      🏠 Setting override for home days target: {self.default_home_days_target_override}")

        # 3. Handling special cases
        if self._constraint_analysis['scattered_constraints'] > 5:
            print(f"      ⚠️ {self._constraint_analysis['scattered_constraints']} scattered constraints identified")

    def _handle_weekend_only_analysis(self):
        """
        Handles the analysis of "weekend-only soldier" (when is_weekend_only_soldier_flag = True).
        """
        print(f"   🏖️ Handling weekend-only soldier settings for {self.name}")
        
        # Reduce weights in the objective function
        self.reduce_weekend_fairness_weight = True
        self.reduce_home_balance_penalty_weight = True

        # Remove restriction on consecutive base days (weekend soldier can stay many days)
        self.max_base_days_override = 14  # Reasonable maximum of two weeks
        
        print(f"      📊 Reduced weights set for fairness penalties")
        print(f"      📅 Override set for consecutive base days: {self.max_base_days_override}")

    def _report_analysis_results(self):
        """Reports the results of the analysis performed"""
        if not any([self.max_base_days_override, self.max_home_days_override, 
                   self.default_home_days_target_override]):
            print(f"   ✅ {self.name}: No special changes required")
            return
            
        print(f"   📋 {self.name}: Analysis results:")
        
        if self.max_base_days_override:
            print(f"      • Max consecutive base days: {self.max_base_days_override}")
            
        if self.max_home_days_override:
            print(f"      • Max consecutive home days: {self.max_home_days_override}")
            
        if self.default_home_days_target_override:
            print(f"      • Total home days target: {self.default_home_days_target_override}")
            
        if self.reduce_home_balance_penalty_weight:
            print(f"      • Home days balance penalty weight reduced")
            
        if self.reduce_weekend_fairness_weight:
            print(f"      • Weekend fairness penalty weight reduced")

    def get_effective_max_consecutive_base_days(self, default_val: int) -> int:
        """Returns the effective maximum consecutive base days for this soldier"""
        return self.max_base_days_override if self.max_base_days_override is not None else default_val

    def get_effective_max_consecutive_home_days(self, default_val: int) -> int:
        """Returns the effective maximum consecutive home days for this soldier"""
        return self.max_home_days_override if self.max_home_days_override is not None else default_val

    def get_effective_default_home_days_target(self, default_val: int) -> int:
        """Returns the effective home days target for this soldier"""
        return self.default_home_days_target_override if self.default_home_days_target_override is not None else default_val

    def get_constraint_summary(self) -> Dict:
        """Returns a detailed summary of the soldier's constraints"""
        return {
            'name': self.name,
            'id': self.id,
            'total_constraint_days': len(self.raw_constraints),
            'is_exceptional_output': self.is_exceptional_output,
            'is_weekend_only': self.is_weekend_only_soldier_flag,
            'constraint_analysis': self._constraint_analysis,
            'active_overrides': {
                'max_base_days': self.max_base_days_override,
                'max_home_days': self.max_home_days_override,
                'home_days_target': self.default_home_days_target_override,
            },
            'penalty_reductions': {
                'home_balance': self.reduce_home_balance_penalty_weight,
                'weekend_fairness': self.reduce_weekend_fairness_weight,
            }
        }

    def validate_constraints_against_calendar(self, calendar_start: date, calendar_end: date) -> List[str]:
        """
        Checks that all of the soldier's constraints are within the calendar range.
        Returns a list of warnings/errors.
        """
        issues = []
        
        for constraint_date in self.raw_constraints:
            try:
                if constraint_date < calendar_start:
                    issues.append(f"Constraint date {constraint_date} is before the calendar start ({calendar_start})")
                elif constraint_date > calendar_end:
                    issues.append(f"Constraint date {constraint_date} is after the calendar end ({calendar_end})")
            except Exception as e:
                issues.append(f"Error checking date {constraint_date}: {e}")
                
        return issues

    def get_constraint_blocks_info(self) -> List[Dict]:
        """Returns detailed information about the soldier's constraint blocks"""
        if 'constraint_blocks' not in self._constraint_analysis:
            return []
            
        blocks_info = []
        try:
            for start_date, length in self._constraint_analysis['constraint_blocks']:
                end_date = start_date + timedelta(days=length-1)
                blocks_info.append({
                    'start_date': start_date,
                    'end_date': end_date,
                    'length': length,
                    'includes_weekend': any(
                        (start_date + timedelta(days=i)).weekday() == 5 
                        for i in range(length)
                    )
                })
        except Exception as e:
            print(f"⚠️ Error calculating block information for {self.name}: {e}")
            
        return blocks_info

    def __repr__(self):
        flags = []
        if self.is_exceptional_output:
            flags.append("Exceptional")
        if self.is_weekend_only_soldier_flag:
            flags.append("Weekend-only")
        
        flag_str = f" ({', '.join(flags)})" if flags else ""
        constraint_count = len(self.raw_constraints)
        
        return f"Soldier(name='{self.name}', id='{self.id}', constraints={constraint_count}{flag_str})"

    def __str__(self):
        """Readable representation of the soldier"""
        lines = [f"Soldier: {self.name} (ID: {self.id})"]
        
        if self.is_exceptional_output:
            lines.append("  🚨 Marked as exceptional output")
        if self.is_weekend_only_soldier_flag:
            lines.append("  🏖️ Weekend-only soldier")
            
        lines.append(f"  📅 Constraints: {len(self.raw_constraints)} days")
        
        if self._constraint_analysis:
            analysis = self._constraint_analysis
            if analysis['longest_consecutive_block'] > 0:
                lines.append(f"  📊 Longest consecutive block: {analysis['longest_consecutive_block']} days")
            if analysis['weekend_constraints'] > 0:
                lines.append(f"  🏖️ Weekend constraints: {analysis['weekend_constraints']}")
                
        return "\n".join(lines)