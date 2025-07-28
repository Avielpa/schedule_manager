# setup.py
"""
Smart Scheduling System Installation Definition
=====================================

Allows installation of the system as a standalone Python package
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    """Read README file"""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "Advanced Smart Scheduling System for Soldiers"

# Read dependencies from requirements.txt
def read_requirements():
    """Read dependencies from requirements file"""
    requirements = []
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove comments and conditions
                    requirement = line.split("#")[0].strip()
                    if requirement:
                        requirements.append(requirement)
    except FileNotFoundError:
        # Minimum dependencies if no requirements file
        requirements = [
            "ortools>=9.7.2996",
            "pandas>=1.5.0",
            "numpy>=1.21.0",
            "openpyxl>=3.0.0",
            "Django>=4.2.0",
            "djangorestframework>=3.14.0"
        ]
    
    return requirements

# Version information
def get_version():
    """Get system version"""
    version_file = os.path.join(os.path.dirname(__file__), 'algorithms', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.strip().split('=')[1].strip().strip("/")
    return "1.0.0"

setup(
    # Basic package information
    name="intelligent-scheduling-system",
    version=get_version(),
    author="Smart Scheduling System",
    author_email="support@smart-scheduling.com",
    description="Advanced automatic soldier scheduling system",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/intelligent-scheduling",
    
    # Packages and files
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    include_package_data=True,
    package_data={
        "algorithms": [
            "*.py",
            "templates/*.xlsx",
            "static/*",
            "locale/*/LC_MESSAGES/*"
        ],
    },
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "performance": [
            "numba>=0.56.0",
            "memory-profiler>=0.60.0",
            "psutil>=5.8.0",
        ],
        "visualization": [
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "plotly>=5.0.0",
        ],
        "production": [
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0",
            "redis>=4.3.0",
            "celery>=5.2.0",
            "sentry-sdk>=1.9.0",
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "black>=22.0.0",
            "numba>=0.56.0",
            "matplotlib>=3.5.0",
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0",
        ]
    },
    
    # Python requirements
    python_requires=">=3.9",
    
    # Package classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        
    ],
    
    # Keywords
    keywords=[
        "scheduling", "optimization", "military", "workforce", "ortools",
        "constraint-programming", "resource-allocation", "automation"
    ],
    
    # License
    license="MIT",
    
    # Entry Points
    entry_points={
        "console_scripts": [
            "intelligent-scheduling=algorithms.cli:main",
            "schedule-solver=algorithms.cli:solve_command",
            "schedule-export=algorithms.cli:export_command",
            "schedule-validate=algorithms.cli:validate_command",
        ],
        "django.management.commands": [
            "run_scheduling=algorithms.management.commands.run_scheduling:Command",
            "export_schedule=algorithms.management.commands.export_schedule:Command",
            "import_soldiers=algorithms.management.commands.import_soldiers:Command",
        ]
    },
    
    # Additional data files
    data_files=[
        ("share/intelligent-scheduling/examples", [
            "examples/example_usage.py",
            "examples/sample_data.json",
        ]),
        ("share/intelligent-scheduling/docs", [
            "README.md",
            "docs/API.md",
            "docs/TUTORIAL.md",
        ]),
    ],
    
    # ZIP settings
    zip_safe=False,
    
    # Wheel support
    has_ext_modules=lambda: False,
)

# Additional helper functions
def post_install():
    """Post-installation actions"""
    print("🎉 Smart Scheduling System installed successfully!")
    print("📚 For more information: https://github.com/your-org/intelligent-scheduling")
    print("🚀 For quick start: intelligent-scheduling --help")

if __name__ == "__main__":
    # Installation with message
    import sys
    
    if "install" in sys.argv:
        print("🔧 Installing Smart Scheduling System...")
        print("📋 Installing dependencies...")
        
    # Run installation
    setup()
    
    # Post-installation message
    if "install" in sys.argv:
        post_install()