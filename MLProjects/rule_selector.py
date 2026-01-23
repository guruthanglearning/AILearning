"""
AI Prompting Rule Selector Tool

This interactive tool helps users select appropriate prompting rules and templates
for their AI/ML tasks based on the comprehensive rule system defined in:
- PROMPTING_RULES.md
- PROMPTING_TEMPLATES.md  
- QUICK_RULES_REFERENCE.md

Usage:
    python rule_selector.py
"""

from typing import List, Dict, Tuple
import os

class PromptingRuleSelector:
    """Interactive tool for selecting appropriate AI prompting rules and templates."""
    
    def __init__(self):
        """Initialize the rule selector with predefined categories and rules."""
        self.rule_categories = {
            "1": "General Project Rules",
            "2": "Machine Learning Specific Rules", 
            "3": "Financial/Stock Analysis Rules",
            "4": "Educational Content Rules",
            "5": "Code Generation Rules",
            "6": "Analysis and Reporting Rules"
        }
        
        self.templates = {
            "1": "Code Generation",
            "2": "ML Model Development", 
            "3": "Stock/Financial Analysis",
            "4": "Learning & Explanation",
            "5": "Debugging & Troubleshooting",
            "6": "Performance Optimization",
            "7": "Feature Engineering",
            "8": "Model Selection",
            "9": "Data Analysis",
            "10": "Production Deployment"
        }
        
        self.quick_combinations = {
            "1": "Code Generation Tasks",
            "2": "ML Model Development",
            "3": "Stock/Financial Analysis", 
            "4": "Learning/Educational Content"
        }

    def display_menu(self) -> None:
        """Display the main menu options."""
        print("\n" + "="*60)
        print("🎯 AI PROMPTING RULE SELECTOR")
        print("="*60)
        print("\nChoose your approach:")
        print("1. 🚀 Quick Rules (Most Common Combinations)")
        print("2. 📝 Template Builder (Structured Prompts)")
        print("3. 🎛️  Custom Rules (Mix & Match Categories)")
        print("4. ℹ️  Help & Information")
        print("5. 🚪 Exit")
        print("\n" + "-"*60)

    def show_quick_rules(self) -> None:
        """Display and allow selection of quick rule combinations."""
        print("\n🚀 QUICK RULE COMBINATIONS")
        print("-"*40)
        
        for key, description in self.quick_combinations.items():
            print(f"{key}. {description}")
        
        choice = input("\nSelect a combination (1-4): ").strip()
        
        if choice in self.quick_combinations:
            self._generate_quick_rule(choice)
        else:
            print("❌ Invalid selection. Please try again.")

    def show_templates(self) -> None:
        """Display available templates for selection."""
        print("\n📝 AVAILABLE TEMPLATES")
        print("-"*40)
        
        for key, description in self.templates.items():
            print(f"{key:2}. {description}")
        
        choice = input("\nSelect a template (1-10): ").strip()
        
        if choice in self.templates:
            self._generate_template(choice)
        else:
            print("❌ Invalid selection. Please try again.")

    def show_custom_rules(self) -> None:
        """Allow custom selection of rule categories."""
        print("\n🎛️  CUSTOM RULE SELECTION")
        print("-"*40)
        
        print("Available rule categories:")
        for key, description in self.rule_categories.items():
            print(f"{key}. {description}")
        
        selections = input("\nSelect categories (e.g., '1,2,5'): ").strip().split(',')
        selections = [s.strip() for s in selections if s.strip() in self.rule_categories]
        
        if selections:
            self._generate_custom_rules(selections)
        else:
            print("❌ No valid categories selected.")

    def _generate_quick_rule(self, choice: str) -> None:
        """Generate quick rule combination based on selection."""
        rule_mappings = {
            "1": {
                "title": "💻 For Code Generation Tasks",
                "rules": "Apply Code Generation + General Project rules from PROMPTING_RULES.md",
                "details": [
                    "- Include proper imports and setup",
                    "- Use type hints and docstrings",
                    "- Add error handling", 
                    "- Provide working examples"
                ]
            },
            "2": {
                "title": "📊 For ML Model Development", 
                "rules": "Apply ML Specific + Code Generation rules from PROMPTING_RULES.md",
                "details": [
                    "- Validate data quality first",
                    "- Include cross-validation",
                    "- Explain feature engineering",
                    "- Provide performance metrics"
                ]
            },
            "3": {
                "title": "💰 For Stock/Financial Analysis",
                "rules": "Apply Financial Analysis + Educational rules from PROMPTING_RULES.md", 
                "details": [
                    "- Use only public data sources",
                    "- Include risk disclaimers",
                    "- Explain backtesting methodology",
                    "- Start with beginner explanations"
                ]
            },
            "4": {
                "title": "🎓 For Learning/Educational Content",
                "rules": "Apply Educational + General rules from PROMPTING_RULES.md",
                "details": [
                    "- Start with conceptual explanation",
                    "- Provide real-world analogies", 
                    "- Include step-by-step breakdowns",
                    "- Mention common pitfalls"
                ]
            }
        }
        
        rule_info = rule_mappings[choice]
        
        print(f"\n✅ SELECTED: {rule_info['title']}")
        print("="*50)
        print(f"Rules: {rule_info['rules']}")
        for detail in rule_info['details']:
            print(detail)
        
        print(f"\n📋 COPY-PASTE FORMAT:")
        print("-"*30)
        print(f"```")
        print(f"Rules: {rule_info['rules']}")
        for detail in rule_info['details']:
            print(detail)
        print(f"\n[Your specific question/request here]")
        print(f"```")

    def _generate_template(self, choice: str) -> None:
        """Generate template based on selection."""
        template_mappings = {
            "1": {
                "name": "Code Generation",
                "template": """Rules: Apply Code Generation + General Project rules from PROMPTING_RULES.md

Task: Create a [FUNCTION/CLASS/MODULE] that [SPECIFIC_FUNCTIONALITY]

Requirements:
- Input: [DESCRIBE_INPUTS]
- Output: [DESCRIBE_OUTPUTS]  
- Performance: [PERFORMANCE_REQUIREMENTS]
- Dependencies: [ALLOWED_LIBRARIES]

Context: [PROVIDE_DOMAIN_CONTEXT]

Question: [YOUR_SPECIFIC_REQUEST]"""
            },
            "2": {
                "name": "ML Model Development",
                "template": """Rules: Apply ML Specific + Code Generation + Educational rules from PROMPTING_RULES.md

Scenario: [DESCRIBE_ML_PROBLEM]
Data: [DESCRIBE_DATASET]
Current Model: [CURRENT_APPROACH]
Performance: [CURRENT_METRICS]
Goal: [TARGET_IMPROVEMENT]

Question: How can I [SPECIFIC_IMPROVEMENT_REQUEST]?"""
            },
            "3": {
                "name": "Stock/Financial Analysis",
                "template": """Rules: Apply Financial Analysis + ML Specific + Educational rules from PROMPTING_RULES.md

Analysis Request: [SPECIFIC_FINANCIAL_QUESTION]
Stock/Asset: [TICKER_SYMBOL_OR_ASSET]
Time Period: [ANALYSIS_TIMEFRAME]
Current Tools: [EXISTING_TOOLS_OR_METHODS]
Risk Tolerance: [RISK_CONSIDERATIONS]

Please include appropriate disclaimers and explain methodology.

Question: [YOUR_DETAILED_REQUEST]"""
            }
        }
        
        # Add more templates for choices 4-10
        if choice in ["4", "5", "6", "7", "8", "9", "10"]:
            template_name = self.templates[choice]
            print(f"\n✅ SELECTED TEMPLATE: {template_name}")
            print("="*50)
            print("📝 Template available in PROMPTING_TEMPLATES.md")
            print("Please refer to the templates file for the complete structure.")
        elif choice in template_mappings:
            template_info = template_mappings[choice]
            print(f"\n✅ SELECTED TEMPLATE: {template_info['name']}")
            print("="*50)
            print("📋 COPY-PASTE FORMAT:")
            print("-"*30)
            print("```")
            print(template_info['template'])
            print("```")
            print("\n💡 Fill in all [BRACKETED] placeholders with your specific details.")

    def _generate_custom_rules(self, selections: List[str]) -> None:
        """Generate custom rule combination based on selections."""
        selected_categories = [self.rule_categories[s] for s in selections]
        
        print(f"\n✅ SELECTED RULE CATEGORIES:")
        print("="*50)
        for i, category in enumerate(selected_categories, 1):
            print(f"{i}. {category}")
        
        print(f"\n📋 COPY-PASTE FORMAT:")
        print("-"*30)
        print("```")
        rule_text = " + ".join(selected_categories)
        print(f"Rules: Apply {rule_text} from PROMPTING_RULES.md")
        print(f"\n[Your specific question/request here]")
        print("```")
        
        print(f"\n💡 TIP: Refer to PROMPTING_RULES.md for detailed rule descriptions.")

    def show_help(self) -> None:
        """Display help information about the prompting system."""
        print(f"\n📚 HELP & INFORMATION")
        print("="*50)
        print(f"This tool helps you select appropriate prompting rules for AI interactions.")
        print(f"\n📁 Available Files:")
        print(f"• PROMPTING_RULES.md      - Complete rule definitions (42 rules)")
        print(f"• PROMPTING_TEMPLATES.md  - Ready-to-use templates (10 templates)")  
        print(f"• QUICK_RULES_REFERENCE.md - Fast access combinations")
        print(f"\n🎯 How to Use:")
        print(f"1. Choose your task type from the menu")
        print(f"2. Copy the generated rule combination")
        print(f"3. Add your specific question/context")
        print(f"4. Use in your AI conversations")
        print(f"\n💡 Benefits:")
        print(f"• Consistent, high-quality AI responses")
        print(f"• Proper documentation and testing")
        print(f"• Educational explanations included")
        print(f"• Safety considerations for financial tasks")

    def run(self) -> None:
        """Run the interactive rule selector."""
        while True:
            self.display_menu()
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                self.show_quick_rules()
            elif choice == "2":
                self.show_templates()
            elif choice == "3":
                self.show_custom_rules()
            elif choice == "4":
                self.show_help()
            elif choice == "5":
                print("\n👋 Thank you for using the AI Prompting Rule Selector!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
            
            input("\nPress Enter to continue...")


def main():
    """Main function to run the prompting rule selector."""
    try:
        selector = PromptingRuleSelector()
        selector.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check that you're in the correct directory with the prompting files.")


if __name__ == "__main__":
    main()