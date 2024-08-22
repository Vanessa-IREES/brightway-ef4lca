### Description:

The contained notebook serves to process and import data from the oekobaudat database into Brightway2, an open-source framework for life cycle assessment (LCA). 
Oekobaudat provides environmental data for for ecological evaluations of buildings by the German Federal Ministry for Housing, Urban Development and Building https://www.oekobaudat.de/en.html.
The notebook facilitates importing oekobaudat data into Brightway2, enabling users to perform LCAs together with other LCA databases. 

**!!! - This import of the oekobaudat is only valid when using the impact categories of EF3.0 EN 15804! - !!!**

The script performs several tasks:

1. Potentially downloads and reads data from a CSV file containing the oekobaudat (database).
2. Processes and aggregates the data into a dataframe to enable the processing of life cycle stages modules according to EN 15804 and end-of-life scenarios.
3. Creates a oekobaudat impact category proxy database to enable correct processing of the data.
4. Writes oekobaudat data, which can have customized module aggregation, into new Brightway2 databases for further analysis also within the Activity-Browser.

### Config file:

- **csv_file_name**: the name of the oekobaudat file, which is located in the current working dir by default.
- **csv_file_url**: the url to download the lates oekobaudat file (will be saved in the current working dir with the configured **csv_file_name**).
- **should_download**: *true* to actually download the oekobaudat file, *false* otherwise.
- **columns_to_include**: the columns which should be read into the dataframe from the oekobaudat file. Be aware there are mandatory columns, such as: UUID, Modul, Szenario, Name (de), Name (en), Bezugsgroesse, Typ. Besides that at least one column containing environmental information should be included to be able to perform LCAs. 
- **dtype**: the types of the above included columns.
- **ic_names**: the included columns that contain environmental data related to impact categories.
- **product_id_label**: the oekobaudat does have a UUID for each product, however these UUIDs are not unique, for a (product, scenario) combination. A life cycle stage module can appear multiple times per product if there are different end-of-life scenarios included. To avoid double inclusion of modules in one product (aka. UUID) there must be a really unique key for the (product,scenario) combination. **product_id_label** is the configured name for this column.
- **mods**: the life cycle stage modules present in the oekobaudat/dataframe. This is configurable to allow multiple pre-aggregated oekobaudat derivation files/dbs.
- **impact_cats**: contains data refering to impact categories of the oekobaudat. One product (UUID) with (chosen) environmental information is imported as activity into brightway. **bs_ref** is the reference of the respective impact category to one ore multiple, **weighted** biosphere flow(s). It enables cross compatibility with other biosphere referring activities. This approach of including the database already in the life cycle inventory allows the oekobaudat data to be included in LCA calculations using (only) impact categories of EF 3.1 EN 15804 together with other databases.
- **obd_impact_cats**: the name of the brightway database which contains the impact categories **impact_cats** of the oekobaudat.

### Impact category proxy database

To enable cross compatibility with other LCA databases we use the impact category proxy database. There, each oekobaudat impact catgory is linked against one representative biosphere entry, the proxy of the impact category. Eg. biogenic global warming potential 100 is represented by a certain amount of biogenic CO2 emission. In order to prevent that a product adds more than one proxy entry reference to the final life cycle assessment result, it is necessary to ensure that only one of all biosphere entries referenced in the proxy database appears with a characterization factor in the final target impact category. Therefore we found unique biosphere entries in all impact categories of EF 3.1 EN 15804. If one impact category does not have such unique biosphere entry, a balancing mechanism must be perform to prevent the proxy adding amounts to more than one impact category result. When a non-unique biosphere entry is used as proxy of the primary impact category, the balancing mechanism substitutes the unintentionally amount in the result of the second impact category. The balancing is performed with another unique biosphere entry of this second impact category. This second impact category therefore contains the correct representation of the result by its unique biosphere entry, its unintentionally added results from the primary impact category and the substitution of this unintentionally added results by another unique biosphere entry as balancing.

### Technical Information 

Technically the ökobaudat database is represented by a CSV file which is encoded in Latin-1 after ISO 8859-1 (International Standardization Organization 1998). It uses a semicolon (';') as the delimiter, and a comma (',') as the decimal separator. The CSV file is parsed into a dataframe using the Python pandas library (The pandas development team 2020). To enhance data processing, the following steps are undertaken:
- The column 'Name (de)' is updated to ensure that it contains English names where the German name is missing.
- The 'Bezugsgroesse' column is processed to ensure data consistency. Non-numeric characters are replaced with 0 and the column is then converted to a float type.
- To handle missing values in float columns, the script selects columns with a float data type (specified by configuration) and replaces NaN values with '0'.
