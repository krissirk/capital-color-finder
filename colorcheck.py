import requests, json, time, csv, os, sys, getopt

# Set variables for processing based on argument passed when script executed
inputArg = str(sys.argv[1])
if inputArg.lower() == "gap":
	processingInputs = ("gap-us_allcaps-color-names.csv", "gp/us")
elif inputArg.lower() == "gapfs":
	processingInputs = ("gapfactory-us_allcaps-color-names.csv", "gpfs/us")
elif inputArg.lower() == "br":
	processingInputs = ("br-us_allcaps-color-names.csv",  "br/us")
elif inputArg.lower() == "brfs":
	processingInputs = ("brfs-us_allcaps-color-names.csv", "brfs/us")
elif inputArg.lower() == "athleta":
	processingInputs = ("athleta_allcaps-color-names.csv", "at/us")
elif inputArg.lower() == "oldnavy":
	processingInputs = ("on-us_allcaps-color-names.csv", "on/us")
else:
	print "Invalid argument -- enter 'gap', 'gapfs', 'br, 'brfs', 'athleta', or 'oldnavy' in order to run this script"
	sys.exit(2)

# Get key value required to access Product Catalog API from environment variable set by secret shell script; assemble header for request
if os.environ.get("MY_API_KEY"):
	MY_API_KEY = str(os.environ.get("MY_API_KEY"))
	apiKey = {"ApiKey": MY_API_KEY}
else:
	print "Environment variable not set - cannot proceed"
	sys.exit(2)

# Function that checks each style color in Product Catalog response to see if its web color description is ALL CAPS, which is an indication that the copy process is incomplete
def evaluateColorsInResponse(styles, output):

	for items in styles:						# Iterate through each style in the response

		for colors in items["styleColors"]:		# Iterate through each child style color within a style

			colorName = colors["colorName"]		# Grab web color description for child style color

			if colorName is None:				# Apparently, it is possible for color descriptions to be blank! In such a situation, force the color variable to all caps 'NULL' value so it gets included in the output file
				colorName = "NULL"

			if colorName == colorName.upper():	# Is the web color description formatted by the business in ALL CAPS? If so, log the product details to output file

				# Grab parent style's inventory status from productStyle API
				if items["_links"]["self"]:
					productStyleUrl = items["_links"]["self"]["href"] + "?appId=kr5v4qu" # Update the 'appId' parameter to identify yourself
					productStyleResponse = requests.get(productStyleUrl)
					productStyleResponse.close()

				# Conditionally variables to write to output file
				if colors["endDate"]:
					colorEndDate = colors["endDate"]
				else:
					colorEndDate = ""

				if colors["searchColor"]:
					searchColor = colors["searchColor"]
				else:
					searchColor = ""

				if productStyleResponse.status_code == 200:	# Sometimes productStyle doesn't return data, so only grab the inventory status and write to output if the response is valid
					isInStock = productStyleResponse.json()["productStyleV1"]["isInStock"]
				else:
					isInStock = ""

				# Write product details to output file
				output.writerow([colors["businessId"].encode('utf-8'), colors["startDate"].encode('utf-8'), colorEndDate, items["name"].encode('utf-8'),
					colorName.encode('utf-8'), colors["promptColorName"].encode('utf-8'), searchColor, isInStock])

	return

print "Start: ", time.asctime( time.localtime(time.time()) )	#Log script start time to console

# Product Catalog API url to access all active and approved products for a business unit; do not need SKUs, so excluding them from the response makes things go faster
apiUrl = "https://api.gap.com/commerce/product-catalogs/catalog/%s?&size=222&active=true&approvalStatus=APPROVED&includeSkus=false" % (processingInputs[1])	

# Prepare output file, write header row
csvfile = open (processingInputs[0], "wb") 
reportwriter = csv.writer(csvfile)
reportwriter.writerow(["styleColorNumber","colorStartDate","colorEndDate","styleName","webColorDescription","promptColorName","searchColor","styleInventoryStatus"])

# Initial Product Catalog API request in the script - this gets the first batch of products processed...and determines how many total pages need to be iterated through
catalogResponse = requests.get(apiUrl, headers=apiKey)
catalogResponse.close()
apiStatusCode = catalogResponse.status_code

# Make sure initial request is successful; if not, re-request until successful response achieved...this block could probably be a function
while apiStatusCode != 200:
	print apiUrl, " - ", apiStatusCode, ": ", catalogResponse.elapsed
	catalogResponse = requests.get(apiUrl, headers=apiKey)
	catalogResponse.close()
	apiStatusCode = catalogResponse.status_code

evaluateColorsInResponse(catalogResponse.json()["_embedded"]["styles"],reportwriter)	# Processing of initial Product Catalog response

pages = catalogResponse.json()["page"]["totalPages"]		# Grab total number of pages in Product Catalog API response
nextLink = catalogResponse.json()["_links"]["next"]["href"]	# Grab link for next Product Catalog page to process

print "Total pages to process: ", pages	# Log total number of pages that need to be processed to the console

x = 1	# Counter for while loop

# Process all remaining pages of Product Catalog response
while x < pages:

	# Make next request of Product Catalog
	catalogResponse = requests.get(nextLink, headers=apiKey)	
	catalogResponse.close()
	apiStatusCode = catalogResponse.status_code

	# Make sure each request is successful; if not, re-request until successful response achieved...this block could probably be a function
	while apiStatusCode != 200:
		print nextLink, " - ", apiStatusCode, ": ", catalogResponse.elapsed
		catalogResponse = requests.get(nextLink, headers=apiKey)
		catalogResponse.close()
		apiStatusCode = catalogResponse.status_code

	evaluateColorsInResponse(catalogResponse.json()["_embedded"]["styles"],reportwriter)	# Processing of next request

	# Grab 'next' pagination link for subsequent request until the data element is no longer in the response
	if "next" in catalogResponse.json()["_links"]:
		nextLink = catalogResponse.json()["_links"]["next"]["href"]

	# Log progress to console & increment counter
	print x, "pages processed" 								
	x += 1

csvfile.close()												# Close output file
print "End: ", time.asctime( time.localtime(time.time()) )	# Log script completion ending time to console