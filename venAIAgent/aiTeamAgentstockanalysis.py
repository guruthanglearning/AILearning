from phi.agent import Agent
from phi.model.groq import Groq
from phi.model.openai import OpenAIChat
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo

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
print ("Web Agent - ")
WebAgent = Agent(name="Web Agent",
                #model=OpenAIChat(id="gpt-4o-mini"),
                model=Groq(id="llama-3.3-70b-versatile"),
                tools=[DuckDuckGo()],
                #instructions=["Always include sources"],
                markdown=False,
                show_tool_calls=False
                #debug_mode=False
                )

print ("Finance Agent - ")
FinanceAgent = Agent(name="Finance Agent",
                #model=OpenAIChat(id="gpt-4o-mini"),
                model=Groq(id="llama-3.3-70b-versatile"),
                tools=[YFinanceTools(stock_price=True,analyst_recommendations=True)],
                #instructions=["Show Stock Price in table"],
                markdown=False,
                show_tool_calls=False
                #debug_mode=False
                )


print ("Team of Agent - ")
teamagents = Agent(team=[WebAgent],
                   #model=Groq(id="llama-3.3-70b-versatile"),
                   model=OpenAIChat(id="gpt-4o-mini"),
                    instructions=["Always include sources","Analysts predication for this quarter earnings", "Show the stock price result in the table format"],
                    markdown1=False,
                    show_tool_calls=False
                    #debug_mode=False,
                )
teamagents.print_response("Summarize included source and stock price for NVDA in table format", stream=True) 