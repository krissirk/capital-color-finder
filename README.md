# capital-color-finder
This Python script identifies products in the Gap Inc. eComm catalogs whose color descriptions are ALL CAPS or feature numeric digits, which are not a user-friendly or "on-brand" formats.

To execute this script, make sure an environment variable "MY_API_KEY" with your personal API key value exists your session. If you do not have an API key, contact GAPINC-COMMERCE-API-DG@gap.com.

Then run "colorcheck.py" along with one of the following valid arguments:
- "athleta" (for products on www.athleta.com)
- "br" (for products on www.bananarepublic.com)
- "brfs" (for products on www.bananarepublicfactory.com)
- "gap" (for products on www.gap.com)
- "gapfs" (for products on www.gapfactory.com)
- "oldnavy" (for products on www.oldnavy.com)

Open the resulting .csv file to see the results.
