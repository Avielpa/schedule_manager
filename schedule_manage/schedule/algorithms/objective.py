"""
🎯 Objective Function Module - V9.0
Centralizes all objective function components and manages optimization
"""

from typing import List, Dict, Any, TYPE_CHECKING
from ortools.sat.python import cp_model

if TYPE_CHECKING:
    from .solver import SmartScheduleSoldiers


class ObjectiveManager:
    """Class for managing the objective function"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.objective_terms: List[Any] = []
        self.objective_breakdown = {
            'shortage_penalties': [],
            'excess_penalties': [],
            'block_penalties': [],
            'fairness_penalties': [],
            'weekend_bonuses': [],
            'minimum_work_penalties': [],
            'long_block_penalties': [],
            'other_penalties': []
        }
        
    def add_term(self, term, category: str = 'other_penalties', 
                description: str = '') -> None:
        """
        Adds a component to the objective function
        
        Args:
            term: The component to add
            category: Category of the component
            description: Description of the component
        """
        self.objective_terms.append(term)
        
        if category in self.objective_breakdown:
            self.objective_breakdown[category].append({
                'term': term,
                'description': description
            })
        else:
            self.objective_breakdown['other_penalties'].append({
                'term': term,
                'description': description
            })
    
    def add_shortage_penalty(self, shortage_var, penalty_value: int, 
                           description: str = '') -> None:
        """
        Adds a shortage penalty
        
        Args:
            shortage_var: Shortage variable
            penalty_value: Penalty value
            description: Description of the penalty
        """
        term = shortage_var * penalty_value
        self.add_term(term, 'shortage_penalties', 
                     f"{description} - penalty {penalty_value:,}")
    
    def add_excess_penalty(self, excess_var, penalty_value: int,
                          description: str = '') -> None:
        """
        Adds an excess penalty
        
        Args:
            excess_var: Excess variable
            penalty_value: Penalty value
            description: Description of the penalty
        """
        term = excess_var * penalty_value
        self.add_term(term, 'excess_penalties',
                     f"{description} - penalty {penalty_value:,}")
    
    def add_block_penalty(self, block_var, penalty_value: int,
                         description: str = '') -> None:
        """
        Adds a block penalty
        
        Args:
            block_var: Block variable
            penalty_value: Penalty value
            description: Description of the penalty
        """
        term = block_var * penalty_value
        self.add_term(term, 'block_penalties',
                     f"{description} - penalty {penalty_value:,}")
    
    def add_fairness_penalty(self, fairness_var, penalty_value: int,
                            description: str = '') -> None:
        """
        Adds a fairness penalty
        
        Args:
            fairness_var: Fairness variable
            penalty_value: Penalty value
            description: Description of the penalty
        """
        term = fairness_var * penalty_value
        self.add_term(term, 'fairness_penalties',
                     f"{description} - penalty {penalty_value:,}")
    
    def add_weekend_bonus(self, weekend_var, bonus_value: int,
                         description: str = '') -> None:
        """
        Adds a weekend bonus
        
        Args:
            weekend_var: Weekend variable
            bonus_value: Bonus value (should be negative)
            description: Description of the bonus
        """
        term = weekend_var * bonus_value
        self.add_term(term, 'weekend_bonuses',
                     f"{description} - bonus {abs(bonus_value):,}")
    
    def add_minimum_work_penalty(self, work_var, penalty_value: int,
                                description: str = '') -> None:
        """
        Adds a minimum work penalty
        
        Args:
            work_var: Work variable
            penalty_value: Penalty value
            description: Description of the penalty
        """
        term = work_var * penalty_value
        self.add_term(term, 'minimum_work_penalties',
                     f"{description} - penalty {penalty_value:,}")
    
    def add_long_block_penalty(self, long_block_var, penalty_value: int,
                              description: str = '') -> None:
        """
        Adds a long block penalty
        
        Args:
            long_block_var: Long block variable
            penalty_value: Penalty value
            description: Description of the penalty
        """
        term = long_block_var * penalty_value
        self.add_term(term, 'long_block_penalties',
                     f"{description} - penalty {penalty_value:,}")
    
    def set_objective(self) -> None:
        """
        Sets the objective function in the model
        """
        if not self.objective_terms:
            print("⚠️ Warning: No components in the objective function")
            return
        
        print("✨ Setting objective function...")
        total_terms = len(self.objective_terms)
        
        # Define the objective: minimize the sum of all components
        self.model.Minimize(sum(self.objective_terms))
        
        print(f"    📊 Total {total_terms} components in the objective function")
        self._print_objective_breakdown()
    
    def _print_objective_breakdown(self) -> None:
        """
        Prints a breakdown of objective function components
        """
        print("    📈 Objective function components breakdown:")
        
        for category, terms in self.objective_breakdown.items():
            if terms:
                category_names = {
                    'shortage_penalties': 'Shortage Penalties',
                    'excess_penalties': 'Excess Penalties',
                    'block_penalties': 'Block Penalties',
                    'fairness_penalties': 'Fairness Penalties',
                    'weekend_bonuses': 'Weekend Bonuses',
                    'minimum_work_penalties': 'Minimum Work Penalties',
                    'long_block_penalties': 'Long Block Penalties',
                    'other_penalties': 'Other Penalties'
                }
                
                category_name = category_names.get(category, category)
                print(f"        🔸 {category_name}: {len(terms)} components")
    
    def get_objective_summary(self) -> dict:
        """
        Returns a summary of the objective function
        
        Returns:
            dict: Summary of the objective function
        """
        summary = {
            'total_terms': len(self.objective_terms),
            'categories': {}
        }
        
        for category, terms in self.objective_breakdown.items():
            summary['categories'][category] = {
                'count': len(terms),
                'descriptions': [term['description'] for term in terms if term['description']]
            }
        
        return summary
    
    def validate_objective(self) -> bool:
        """
        Ensures the objective function is valid
        
        Returns:
            bool: True if the objective function is valid
        """
        if not self.objective_terms:
            print("❌ Error: Objective function is empty")
            return False
        
        # Check that there is at least one component in each important category
        critical_categories = ['shortage_penalties', 'block_penalties', 'minimum_work_penalties']
        missing_critical = []
        
        for category in critical_categories:
            if not self.objective_breakdown[category]:
                missing_critical.append(category)
        
        if missing_critical:
            print(f"⚠️ Warning: Missing critical components: {missing_critical}")
        
        # Check that there is a balance between penalties and bonuses
        penalties_count = sum(
            len(terms) for category, terms in self.objective_breakdown.items()
            if 'penalties' in category
        )
        bonuses_count = len(self.objective_breakdown['weekend_bonuses'])
        
        if penalties_count == 0:
            print("❌ Error: No penalties in the objective function")
            return False
        
        print(f"✅ Objective function is valid: {penalties_count} penalties, {bonuses_count} bonuses")
        return True
    
    def reset_objective(self) -> None:
        """
        Resets the objective function
        """
        self.objective_terms.clear()
        for category in self.objective_breakdown:
            self.objective_breakdown[category].clear()
        print("🔄 Objective function reset")
    
    def get_category_terms_count(self, category: str) -> int:
        """
        Returns the number of components in a specific category
        
        Args:
            category: Category name
            
        Returns:
            int: Number of components
        """
        return len(self.objective_breakdown.get(category, []))
    
    def has_critical_penalties(self) -> bool:
        """
        Checks if there are critical penalties
        
        Returns:
            bool: True if there are critical penalties
        """
        critical_categories = ['shortage_penalties', 'block_penalties', 'minimum_work_penalties']
        return any(self.objective_breakdown[category] for category in critical_categories)
    
    def get_terms_by_category(self, category: str) -> List[dict]:
        """
        Returns components by category
        
        Args:
            category: Category name
            
        Returns:
            List[dict]: List of components
        """
        return self.objective_breakdown.get(category, []).copy()