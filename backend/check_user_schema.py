
import sys
import os


# backend path is already in python path in docker


from app.models.user import User, Country, LocationPreference
from app.schemas.user import UserSchema

def check_schema():
    print("Checking Pydantic Models...")
    try:
        # Check Country model
        country = Country(code="US", name="United States", currency="USD")
        print(f"Country model OK: {country}")
        
        # Check LocationPreference with Country object
        loc_pref = LocationPreference(country=country)
        print(f"LocationPreference model OK: {loc_pref}")
        
        # Check User Profile schema
        print("\nChecking MongoDB Schema...")
        validator = UserSchema.get_validator()
        country_prop = validator['$jsonSchema']['properties']['profile']['properties']['location_preferences']['properties']['country']
        print(f"MongoDB Country Validator: {country_prop}")
        
        if country_prop['bsonType'] == 'object' and 'code' in country_prop['properties']:
            print("SUCCESS: MongoDB schema updated correctly.")
        else:
            print("FAILURE: MongoDB schema mismatch.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_schema()
