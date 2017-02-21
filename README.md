# capital-color-finder
This Python script identifies products in the Gap Inc. eComm catalogs whose color descriptions are in ALL CAPS, which is not a user friendly or "on-brand" format.

To execute this script, make sure an environment variable "MY_API_KEY" with your personal API key value exists. If you do not have an API key, contact GAPINC-COMMERCE-API-DG@gap.com.

Then run "colorcheck.py" along with one of the following valid arguments:
- "athleta" (for products on www.athleta.com)
- "br" (for products on www.bananarepublic.com)
- "brfs" (for products on www.bananarepublicfactory.com)
- "gap" (for products on www.gap.com)
- "gapfs" (for products on www.gapfactory.com)
- "oldnavy" (for products on www.oldnavy.com)

Open the resulting .csv file to see the results.
