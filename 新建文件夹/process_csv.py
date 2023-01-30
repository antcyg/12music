import pickle


def load_market_processed_pickle(csv_path):
    with open(csv_path, 'rb') as csv_file:
        data = pickle.load(csv_file)
    res = {key: value[2] for key, value in data.items() if key != 'stock'}
    res['stock'] = data['stock']
    return res


if __name__ == '__main__':
    data = load_market_processed_pickle('raw_data_20230119140020.pickle')
