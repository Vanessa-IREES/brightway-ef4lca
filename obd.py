from bw2data import Database, databases
import pandas as pd
import numpy as np
import re
import os


def read_obd(config, obd_path):
    """read the obd from the obd csv file.
    """
    print(f'Read OBD (encoding="latin1", delimiter=";",decimal=",")...')
    try:
        df = pd.read_csv(obd_path, encoding='latin1', delimiter=';', decimal=',',
                         usecols=config['columns_to_include'], dtype=config['dtype'])
        return df
    except ValueError as e:
        print(f'PARSE-ERROR {e}')


def prepare_obd_data(df):
    """ Methods which are necessary to preocess obd programmatically.
    """
    print(f'Prepare OBD data...')
    # Replace all NaN values with empty strings
    df['Name (en)'] = df['Name (en)'].replace({np.nan: ''})
    df['Szenario'] = df['Szenario'].replace({np.nan: ''})
    # df['Bezugseinheit'] = df['Bezugseinheit'].replace({np.nan: ''}) #should be error without unit

    # replace name (en) with german name if no english name is available
    df['Name (en)'] = df.apply(lambda row: str(row['Name (de)'])
                               if row['Name (en)'] == '' else str(row['Name (en)']), axis=1)

    # TODO sanity
    df['Bezugsgroesse'] = df['Bezugsgroesse'].replace(
        r'[^0-9.]', '0', regex=True).astype(float)

    # replace all other floats with 0 if nan
    # Identify columns with float data type
    float_columns = df.select_dtypes(include=['float']).columns
    # Replace 0 with NaN in float columns
    df[float_columns] = df[float_columns].replace(np.nan, 0)
    # print(float_columns)

    # check types
    return df


def unfold_scenarios(config, df):
    """ builds actually unique products (by scenario) by building a config["product_id_label"] named column which holds UUID and Scenario. This is necessary to prevent wrong aggregations over UUID only.
    """

    print(f'Unfold OBD scenarios...')

    # we need to make dedicated products of the scenarios
    # create new combined row holding uuid + scenario
    # copy all remaining modules of base case to each scenario
    # remove base case

    # this id is important as it refers to unique products (ie.: uuid + scenario)
    product_id_label = config['product_id_label']

    # Concatenate rows by label and append the new row to the DataFrame with label: product_id_label
    df[product_id_label] = df.apply(
        lambda row: row['UUID'] + ('#' if row['Szenario'] != '' else '') + row['Szenario'], axis=1)

    # Identify Products with Scenarios
    products_with_scenarios = df[df['UUID'] != df[product_id_label]]

    # List of products which have scenarios
    unique_products_with_scenarios = products_with_scenarios['UUID'].unique()

    # Select Base Rows for Each Product
    base_rows = df[df['UUID'] == df[product_id_label]]
    # print(base_rows)

    # Remove rows referring to products with scenarios
    df_filtered = df[~df['UUID'].isin(unique_products_with_scenarios)]

    # Identify Relevant Scenarios for Each Product (distinct rows)
    relevant_scenarios = products_with_scenarios.drop_duplicates(subset=[
                                                                 product_id_label])

    # print(relevant_scenarios)

    # Step 4: Copy Base Rows for Each Scenario
    frames = []
    for _, scenario in relevant_scenarios.iterrows():
        # all rows with filled szen col for a certain product_id_label
        temp_scenario = df[(df['UUID'] == scenario['UUID']) & (
            df[product_id_label] == scenario[product_id_label])]
        # modules containe in scenario
        scen_mods = set(temp_scenario['Modul'])
        # base rows to fill up scenario with remaining modules (contain only modules which aren't already in scenario)
        temp_base = base_rows[(base_rows['UUID'] == scenario['UUID']) & (
            ~base_rows['Modul'].isin(scen_mods))].copy()
        temp_base[product_id_label] = scenario[product_id_label]
        temp_base["Szenario"] = scenario["Szenario"]

        frames.append(temp_base)
        frames.append(temp_scenario)

    final_df = pd.concat(frames, ignore_index=True)

    # Concatenate df_filtered with final_df
    df = pd.concat([df_filtered, final_df], ignore_index=True)
    df.drop_duplicates()
    return df


def insert_dummy_rows(config, df):
    """
    Insert dummy rows so that each product (identified by product_id_label) has all modules.
    """

    print(f'Insert dummy rows for modules...')

    product_id_label = config['product_id_label']
    all_product_ids = df[product_id_label].unique()
    for product_id in all_product_ids:
        product_id_rows = df[df[product_id_label] == product_id]
        existing_modules = product_id_rows['Modul'].unique()
        missing_modules = set(config['mods']) - set(existing_modules)
        for module in missing_modules:

            # Series is a one-dimensional labeled array.
            dummy_row = pd.Series(index=df.columns, dtype='object')
            for col in df.columns:
                # print(f'col is {col}')
                if col == 'Modul':
                    # print(f'add modul: {aspect}')
                    dummy_row[col] = module
                elif col in config['ic_names']:
                    dummy_row[col] = 0.0
                else:
                    # print(f'copy row entry:{product_id_rows[col].iloc[0]} of {product_id_rows[col]')
                    dummy_row[col] = product_id_rows[col].iloc[0]

            # Append the aggregated row to the dataframe
            df = pd.concat([df, pd.DataFrame([dummy_row])], ignore_index=True)
    print('done inserting dummy rows')
    return df


pattern = r'([A-Z]\d)-([A-Z]\d)'


def map_value(item, map):
    if item not in map:
        raise KeyError(f'Key "{item}" not found in mapping dictionary')
    return map[item]


# eg.: ['A1-A3', 'A4', 'A5']
def format_aggregation_key(config, modules):
    """ builds keys from passed modules which reflect the sequences which can be build from the passed modules. 
    To do this the modules are ordered (in config["mods"]) and each can be represented by an integer.
    """
    mc = config['mods'][:]

    # replace modules in mc with aggregations: ['A1', 'A2, 'A3', 'A4', 'A5'] -> ['A1-A5']
    # this changes the copy (mc) of the initially read modules list
    for m in modules:
        match = re.search(pattern, m)
        if match:
            fir = mc.index(match.group(1))
            sec = mc.index(match.group(2))
            del mc[fir:fir+(sec-fir+1)]
            mc[fir:fir] = [m]

    map = {}
    map_i_s = {}
    map_i_t = {}

    for idx, val in enumerate(mc):
        # setup map (there is prob a better way to do this)
        map[val] = idx

        # performance is irrelevant
        match2 = re.search(pattern, val)
        # puts right vals in start and terminal maps (to construct righgt aggregation keys eventually)
        if match2:
            map_i_s[idx] = match2.group(1)
            map_i_t[idx] = match2.group(2)
        else:
            map_i_s[idx] = val
            map_i_t[idx] = val

    # map passed params to integers and sort them
    aggregation_idxs = [map_value(item, map) for item in modules]
    lst = sorted(int(a) for a in aggregation_idxs)

    # find continuous sequences of lst
    ranges = []
    start = prev = lst[0]
    for n in lst[1:]:
        if n - 1 == prev:  # part of the sequence
            prev = n
        else:  # not part of the sequence
            if start == prev:
                ranges.append(map_i_s[start])
            else:
                ranges.append(f'{map_i_s[start]}-{map_i_t[prev]}')
            start = prev = n
    if start == prev and map_i_s[start] == map_i_t[prev]:
        ranges.append(map_i_s[start])
    else:
        ranges.append(f'{map_i_s[start]}-{map_i_t[prev]}')

    res = ';'.join(ranges)
    # print(res)
    return res


def agg_floats(df, float_cols):
    """ aggregates floats of all passed columns of the passed dataframe and returns the result as Series.
    """
    # Series is a one-dimensional labeled array capable of holding any data type (integers, strings, floating point numbers, Python objects, etc.). The axis labels are collectively referred to as the index.
    result = pd.Series(index=df.columns, dtype='object')
   # print(result.dtype)
    for col in df.columns:
        # print(f'col is {col}')
        if col in float_cols:
            result[col] = df[col].sum()
        else:
            result[col] = df[col].iloc[0]
    return result


def custom_aggregate(config, df, modules, delete_original=False):
    """function lets you make custom aggregations of modules. Be aware that the passed modules must be in the dataframe which is passed. Passing ['A1-A3', 'A4', 'A5'] as modules (to be aggregated), the resulting aggregation is the sum of the single module columns: 'A1-A3', 'A4' and 'A5'. The aggregate will be labeled as 'A1-A5'. If delete_original is true the original modules: 'A1-A3', 'A4' and 'A5' will be removed from the dataframe.  """

    product_id_label = config['product_id_label']
    # Create the aggregation key (e.g., '1-3')
    aggregation_key = format_aggregation_key(config, modules)
    print(
        f'aggregate with modules: {modules} and key is: {aggregation_key}; will delete: {delete_original}')

    all_product_ids = df[product_id_label].unique()

    for product_id in all_product_ids:
        # Filter rows for the current product
        product_df = df[df[product_id_label] == product_id]

        # Check if the aggregation already exists for this product (eg. A1-A3 is contained by default)
        if aggregation_key not in product_df['Modul'].values:

            # Further filter rows for the specified aspects
            filter_mask = (df[product_id_label] ==
                           product_id) & df['Modul'].isin(modules)
            data_to_aggregate = df[filter_mask]

            if not data_to_aggregate.empty:
                # print(data_to_aggregate)
                aggregated_data = agg_floats(
                    data_to_aggregate, config['ic_names'])
                aggregated_data['Modul'] = aggregation_key
                # print(aggregated_data)
                # Append the aggregated row to the dataframe
                df = pd.concat(
                    [df, pd.DataFrame([aggregated_data])], ignore_index=True)

        # wrong redundant modules sometimes thus apply to all
        # Optionally delete the original rows that were aggregated (or for initial setup A1-A3 aggregation is contained by default, so dummy A1,A2,A3 must be removed)
        if delete_original:
            # cannot reuse filter mask bc. concatication
            filter_mask_2 = (df[product_id_label] ==
                             product_id) & df['Modul'].isin(modules)
            if filter_mask_2.any():
                df = df[~filter_mask_2]

    return df


def import_impact_categories_db(config, biosphere_db):
    """ Import the obd impact categories so that they can be referenced as exchanges.
    """

    print(f'Import impact categories as db to brightway...')

    # add/overwrite new database with impact cats
    if databases.get(config['obd_impact_cats']):
        del databases[config['obd_impact_cats']]
    else:
        print(f'{config["obd_impact_cats"]} not in databases')

    obd_db = Database(config['obd_impact_cats'])

    cc_dict = {}
    for i in range(len(config['ic_names'])):
        ic_name = config['ic_names'][i]
        code = f'bobd{i}'
        if ic_name in config['ic_biosphere_map']:
            print(f'Found mapping for: {ic_name}')
            entry = {
                'name': ic_name,
                'exchanges': [],
                'unit': config['obd_units'][i],
                'categories': (config['obd_cats'][i]),
                'type': 'process',
                'production amount': 1.0,
                'location': 'GLO',
                'code': code
            }
            for mapping in config['ic_biosphere_map'][ic_name]:
                bs_dic = biosphere_db.get(mapping['code']).as_dict()
                entry['exchanges'].append({
                    'amount': mapping['amount'],
                    'name': bs_dic['name'],
                    'database': 'biosphere3',
                    'type': 'biosphere',  # this must be type biosphere!
                    'unit': bs_dic['unit'],
                    'input': ('biosphere3', mapping['code']),
                    'categories': bs_dic['categories']
                })
            cc_dict[(config['obd_impact_cats'], code)] = entry
            # print(f"ENTRIES of {ic_name} are {entry['exchanges']}")
    obd_db.write(cc_dict)

# print(cc_dict)


def prepare_db_dict(config, db_name, data_frame, id_label, ic_names):
    """ Prepare obd table for import as brightway db, ie. all products are registered as activity and the respective impact categories are registered as exchanges.
    """

    print(
        f'Prepare data for import, db name is {db_name}, dataframe is:\n {data_frame}...')

    print(f'Will link these impact categories biosphere refs: {ic_names}.')

    db_dict = {}
    for index, row in data_frame.iterrows():
        te = {
            'id': row[id_label],
            'name': row['Name (en)'],
            'exchanges': [],
            'unit': row['Bezugseinheit'],
            'categories': ('OBD'),
            'relfac': row['Bezugsgroesse'],
            'type': 'process',
            'production amount': row['Bezugsgroesse'],
            'location': 'DE',
            'reference product': f"{row['Name (en)']}, Scenario: {row['Szenario']}, Aggregation: {row['Modul']}",
            'comment': f"Typ: {row['Typ']}\nScenario: {row['Szenario']}\nAggregation: {row['Modul']}",
            'UUID': row['UUID']
        }
        for _, ic_name in enumerate(ic_names):
            if ic_name in config['ic_biosphere_map']:
                idx = config['ic_names'].index(ic_name)
                te['exchanges'].append({
                    'amount': row[ic_name],
                    'name': ic_name,
                    'database': config['obd_impact_cats'],
                    'type': 'technosphere',  # must be biosphere/technosphere
                    'unit': config['obd_units'][idx],
                    'input': (config['obd_impact_cats'], f'bobd{idx}'),
                    'categories': [config['obd_cats'][idx]]})

        db_dict[(db_name, row[id_label])] = te
    return db_dict


def write_new_db(db_name, db_dict):
    """ write the prepared dict as brightway db. 
    Method checks whether equally named db already exists and DELETES it if so.
    """

    # dir(databases)
    if databases.get(db_name):
        del databases[db_name]
    else:
        print(f'{db_name} not in databases')

    print(f'now import {db_name}.')
    db = Database(db_name)
    db.write(db_dict)


def prepare_and_write_new_db(config, db_name, data_frame, id_label, ic_names):
    write_new_db(db_name, prepare_db_dict(
        config, db_name, data_frame, id_label, ic_names))


def reformat_cfs(ds):
    # https://github.com/brightway-lca/brightway2-io/blob/main/bw2io/importers/base_lcia.py#L94
    # Note: This assumes no uncertainty or regionalization
    return [((obj['input']), obj['amount']) for obj in ds]


def read_and_prepare_obd_data(config, data_dir):
    """ read and prepare obd csv as dataframe which can be properly processed/used.
    """
    data_dir_path = os.path.join(data_dir, config['csv_file_name'])
    df = read_obd(config, data_dir_path)
    df = prepare_obd_data(df)
    df = unfold_scenarios(config, df)
    # this might take a while
    df = insert_dummy_rows(config, df)

    # this might take a while
    # this is included in general data preparation, since obd itself declars often only 'A1-A3' hence we cannot use these modules singularily.
    df = custom_aggregate(config, df, ['A1', 'A2', 'A3'], True)
    return df
