from sqlalchemy.orm import Session
from app.models.government_scheme import GovernmentScheme

DEFAULT_SCHEMES = [
    {"name":"Soil Health Card","state":None,"description":"Official Soil Health Card information and soil testing services.","url":"https://soilhealth.dac.gov.in/","active":True},
    {"name":"PM-KISAN","state":None,"description":"Official PM-KISAN information and farmer services.","url":"https://pmkisan.gov.in/","active":True},
    {"name":"Agriculture & Farmers Welfare","state":None,"description":"Central agriculture department information and farmer resources.","url":"https://agriwelfare.gov.in/","active":True},
    {"name":"ICAR","state":None,"description":"Indian Council of Agricultural Research information and research resources.","url":"https://icar.gov.in/","active":True},
]

def seed_schemes(db: Session):
    for item in DEFAULT_SCHEMES:
        if not db.query(GovernmentScheme).filter(GovernmentScheme.name == item["name"]).first():
            db.add(GovernmentScheme(**item))
    db.commit()
