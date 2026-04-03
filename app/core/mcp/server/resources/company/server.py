from fastmcp import FastMCP

try:
    from .company_data import (
        CULTURE_AND_COMMUNITY,
        HISTORY_AND_ORIGINS,
        ORGANIZATION_AND_LEADERSHIP,
        PRODUCTS_AND_SOLUTIONS,
        STRATEGY_AND_INNOVATION,
    )
except ImportError:
    from company_data import (
        CULTURE_AND_COMMUNITY,
        HISTORY_AND_ORIGINS,
        ORGANIZATION_AND_LEADERSHIP,
        PRODUCTS_AND_SOLUTIONS,
        STRATEGY_AND_INNOVATION,
    )

company_server = FastMCP("CompanyResources")


@company_server.resource("rocscience://company/history")
def history() -> str:
    """Get Rocscience history and origins."""
    return HISTORY_AND_ORIGINS.strip()


@company_server.resource("rocscience://company/organization")
def organization() -> str:
    """Get Rocscience organization info, scale, and leadership."""
    return ORGANIZATION_AND_LEADERSHIP.strip()


@company_server.resource("rocscience://company/products")
def products() -> str:
    """Get Rocscience product ecosystem details."""
    return PRODUCTS_AND_SOLUTIONS.strip()


@company_server.resource("rocscience://company/strategy")
def strategy() -> str:
    """Get Rocscience M&A strategy and innovation initiatives."""
    return STRATEGY_AND_INNOVATION.strip()


@company_server.resource("rocscience://company/culture")
def culture() -> str:
    """Get Rocscience corporate culture and community events."""
    return CULTURE_AND_COMMUNITY.strip()
