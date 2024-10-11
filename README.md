**XML_Generator**

This python script is designed to continually update an editors timeline with new VFX comps from vendors as they are received. 

It accomplishes this by doing the following:
- Scan the production company's server
- Select all comps with a given token, for example "_COMP"
- Organize them by date received
- Populate them onto a timeline which can be imported into Premiere.

The timeline is generated using in/out points and clip properties from a "Template XML". 

i.e. - Export the entire movie as an XML, use this script to reference it, and it will generate new timelines for you based on that cut of the movie.

The date range is currently fed to the script in the form of arguments. 

Example usage is: 
path/to/script.py start_date end_date
path/to/script.py 20240130 20240615      - This will collect all comps from Jan 30th 2024, until June 15th 2024
