"""
🔒 Constraints Module - V9.0
Centralizes all different types of algorithm constraints
"""

from .basic import BasicConstraints
from .daily_requirements import DailyRequirementsConstraints
from .minimum_work import MinimumWorkConstraints
from .blocks import BlockConstraints
from .consecutive import ConsecutiveConstraints
from .balance import BalanceConstraints

__all__ = [
    'BasicConstraints',
    'DailyRequirementsConstraints', 
    'MinimumWorkConstraints',
    'BlockConstraints',
    'ConsecutiveConstraints',
    'BalanceConstraints'
]

# Order of constraint application (important to maintain this order!)
CONSTRAINTS_ORDER = [
    'BasicConstraints',
    'DailyRequirementsConstraints',
    'MinimumWorkConstraints',
    'BlockConstraints',
    'ConsecutiveConstraints',
    'BalanceConstraints'
]

def apply_all_constraints(solver_instance):
    """
    Applies all constraints in the correct order
    
    Args:
        solver_instance: The main solver instance
    """
    print("⚙️ Applying all constraints and objectives...")
    
    # Basic constraints - must be first
    basic = BasicConstraints(solver_instance)
    basic.apply()
    
    # Daily requirements constraints
    daily_req = DailyRequirementsConstraints(solver_instance)
    daily_req.apply()
    
    # Minimum work constraints
    min_work = MinimumWorkConstraints(solver_instance)
    min_work.apply()
    
    # Block constraints - after basic variables are set
    blocks = BlockConstraints(solver_instance)
    blocks.apply()
    
    # Consecutive days constraints
    consecutive = ConsecutiveConstraints(solver_instance)
    consecutive.apply()
    
    # Balance and fairness - last
    balance = BalanceConstraints(solver_instance)
    balance.apply()