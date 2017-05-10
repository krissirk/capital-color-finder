import requests, json, time, csv, os, sys

# Initialize dictionary that contains inputs for Product Catalog API requests and output .csv file
brands = 	{"gap": ("gap-us_allcaps-color-names.csv", "gp/us"),
			 "gapfs": ("gapfactory-us_allcaps-color-names.csv", "gpfs/us"),
			 "br": ("br-us_allcaps-color-names.csv",  "br/us"),
			 "brfs": ("brfs-us_allcaps-color-names.csv", "brfs/us"),
			 "athleta": ("athleta_allcaps-color-names.csv", "at/us"),
			 "oldnavy": ("on-us_allcaps-color-names.csv", "on/us")
			}

# Set variables for processing based on argument passed when script executed; exit if no or incorrect argument passed
if len(sys.argv) > 1:
	inputArg = str(sys.argv[1]).lower()

	if inputArg in brands:
		processingInputs = brands[inputArg]
	else:
		print("Invalid argument -- enter 'gap', 'gapfs', 'br, 'brfs', 'athleta', or 'oldnavy' in order to run this script")
		sys.exit(2)
else:
	print("No argument found -- enter 'gap', 'gapfs', 'br, 'brfs', 'athleta', or 'oldnavy' in order to run this script")
	sys.exit(2)

# Get key value required to access Product Catalog API from environment variable set by secret shell script and assemble header for request; exit if variable not set
# Also set custom user-agent info for header
if os.environ.get("MY_API_KEY"):
	MY_API_KEY = str(os.environ.get("MY_API_KEY"))
	CONTACT = str(os.environ.get("CONTACT"))
	myHeader = {"ApiKey": MY_API_KEY,
				"User-Agent": "Color Format Checker Python Script",
				"From": CONTACT
				}
else:
	print("Environment variables not set - cannot proceed")
	sys.exit(2)

##################### FUNCTION DEFINITIONS #####################

# Function that checks each style color in Product Catalog response to see if its web color description is ALL CAPS or numeric
# which is an indication that the copy process is incomplete
def evaluateColorsInResponse(styles, output, page):

	for items in styles:						# Iterate through each style in the response

		for colors in items["styleColors"]:		# Iterate through each child style color within a style

			colorName = colors["colorName"]		# Grab web color description for child style color

			if colorName is None:				# It's possible for color descriptions to be blank! If so, force the color variable to 'NULL' so it gets included in the output file
				colorName = "NULL"

			# If the web color description formatted by the business is in ALL CAPS contains a numeric digit, log the product details to output file
			if (colorName == colorName.upper()) or (any(char.isdigit() for char in colorName)):

				# Grab parent style's inventory status from productStyle API
				if items["_links"]["self"]:
					productStyleUrl = items["_links"]["self"]["href"] + "&appId=kr5v4qu" # Update the 'appId' parameter to identify yourself
					productStyleResponse = requests.get(productStyleUrl)
					productStyleResponse.close()

				# Conditionally set variables to write to output file
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

				# Write product details to output file; response page number recorded to assist with troubleshooting problematic data
				output.writerow([colors["businessId"], colors["startDate"], colorEndDate, items["name"],
					colorName, colors["promptColorName"], searchColor, isInStock, page])

	return

# Function that makes Product Catalog API request until successful response obtained, returns that response
def apiRequest(url):

	apiStatusCode = 0

	try:
		apiResponse = requests.get(url, headers=myHeader, timeout=120)
		apiResponse.close()
		apiStatusCode = apiResponse.status_code
	except:
		None

	# Make sure initial request is successful; if not, re-request until successful response obtained
	while apiStatusCode != 200:

		try:
			print(url, " - ", apiStatusCode, ": ", apiResponse.elapsed)
		except:
			print(url + " done waiting for response - will retry.")

		try:
			apiResponse = requests.get(url, headers=myHeader, timeout=120)
			apiResponse.close()
			apiStatusCode = apiResponse.status_code
		except:
			print(url + " done waiting for response - will retry.")

	return apiResponse

##################### END OF FUNCTION DEFINITIONS ####################

print("Start: ", time.asctime( time.localtime(time.time()) ))	#Log script start time to console

# Product Catalog API url to access all active and approved products for a business unit; do not need SKUs, so excluding them from the response makes things go faster
apiUrl = "https://api.gap.com/commerce/product-catalogs/catalog/{0}?&size=222&active=true&approvalStatus=APPROVED&includeSkus=false".format(processingInputs[1])

# Prepare output file, write header row
csvfile = open (processingInputs[0], "w")
reportwriter = csv.writer(csvfile)
reportwriter.writerow(["styleColorNumber","colorStartDate","colorEndDate","styleName",
					   "webColorDescription","promptColorName","searchColor","styleInventoryStatus","apiPageNumber"])

# Initial Product Catalog API request in the script - this gets the first batch of products to be processed and determines how many total pages need to be iterated through
catalogResponse = apiRequest(apiUrl)

try:
	pages = catalogResponse.json()["page"]["totalPages"]	# Grab total number of pages in Product Catalog API response
	print("Total pages to process: ", pages)				# Log total number of pages that need to be processed to the console

	# Check the initial response for problematic style colors
	evaluateColorsInResponse(catalogResponse.json()["_embedded"]["styles"],reportwriter,0)
	print("1 page processed")

	# Grab URL of 'next' pagination link in Product Catalog response if it exists in order to process during first iteration of while loop
	if "next" in catalogResponse.json()["_links"]:
		nextLink = catalogResponse.json()["_links"]["next"]["href"]
		x = 1	# Initialize counter for while loop that will ensure the entire Product Catalog is processed

	else:
		x = pages + 1 # If no 'next' link, initialize counter such that it doesn't go into the while loop

	except ValueError as err:
		print("Could not process initial response {0} due to error {1}.".format(initialApiUrl, err))

		#  Set variables to 0 to ensure script doesn't enter while loop to process additional responses becuase next URL isn't available
		x = 0
		pages = 0

# Process all remaining pages of Product Catalog response
while x < pages:

	# Make next request of Product Catalog and check the resulting response for problematic style colors
	catalogResponse = apiRequest(nextLink)

	try:
		evaluateColorsInResponse(catalogResponse.json()["_embedded"]["styles"],reportwriter,x)

		# Grab URL of 'next' pagination link for subsequent request until the data element is no longer in the response (which will only happen during final iteration of loop)
		if "next" in catalogResponse.json()["_links"]:
			nextLink = catalogResponse.json()["_links"]["next"]["href"]

		# Increment counter & log progress to console
		x += 1
		print(x, "pages processed")

	except ValueError as err:
		print("Could not process initial response {0} due to error {1}.".format(nextLink, err))

csvfile.close()												# Close output file
print("End: ", time.asctime( time.localtime(time.time()) ))	# Log script completion ending time to console
