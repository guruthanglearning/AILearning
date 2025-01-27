from phi.agent import Agent
from phi.model.groq import Groq
from phi.model.openai import OpenAIChat
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools

load_dotenv()

def get_company_symbol(company: str) -> str:
        """
        Use this function to get the stock symbol for a company.

        Args:
            company (str): The name of the company.

        Returns:
            str: The symbol of the company.
        """        
        company_symbols = {
            "PhiData": "AAPL"            
        }
        return company_symbols.get(company, "Unknown")
           

print ("Stock Analysis Agent")
print ("Lama - ")
stockAgentPhiLama = Agent(model=Groq(id="llama-3.3-70b-versatile"),
                   markdown=False,
                   show_tool_calls=False,
                   debug_mode=False,
                   tools=[YFinanceTools(
                            stock_price=True,
                            technical_indicators=True                           
                         )],                          
                    instructions=["Show Stock Price in table"])
stockAgentPhiLama.print_response("What is the stock price of Apple Inc. (AAPL) today?") 
 
print ("GPT - ")
stockAgentPhiOpenAI = Agent(model=OpenAIChat(id="gpt-4o-mini"),
                    markdown=False,
                    show_tool_calls=False,
                    debug_mode=False,
                    tools=[YFinanceTools(
                           enable_all= True
                         ),get_company_symbol],                          
                    instructions=["Show Stock Price in table","if you don't have the stock symbol please use the get company symbol function"])
stockAgentPhiOpenAI.print_response("What is the stock price of PhiData . (PhiData) today?") 
