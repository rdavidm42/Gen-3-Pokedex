import pandas as pd
import streamlit as st

def find_game(column,dataframe):
    series = []
    for col in column:
        indices = [i for i in range(386) if dataframe[col].str.find('Trade from').iloc[i] == -1]
        series = series + indices
    series = list(set(series))
    return dataframe[['No.','Caught?',*column]].iloc[series]
    
def find_game_nan(column,dataframe):
    series = []
    for col in column:
        indices = [i for i in range(386) if dataframe[col].str.find('Trade from').iloc[i] == -1]
        series.append(dataframe[col].iloc[indices])
    combined = pd.concat(series,axis=1)
    combined[['No.','Caught?']] = dataframe[['No.','Caught?']].loc[combined.index]
    combined = combined[['No.','Caught?']+column]
    return combined.sort_values(by='No.')

def get_dif(columns,dataframe):
    dummy = find_game_nan(columns,dataframe)
    indexes = []
    for column in columns:
        data = dummy[column]
        index = list(data[pd.isna(data)].index)
        indexes.append(index)
    indexes_flat = list(set([x for y in indexes for x in y]))
    return dummy.loc[indexes_flat].sort_values(by='No.')

def get_intersection(columns,dataframe):
    return find_game_nan(columns,dataframe).dropna()

def one_game_exclusive(one,others,dataframe):
    if type(one) == str:
        dummy = get_dif([one]+others,dataframe)
    else:
        dummy = get_dif(one+others,dataframe)
    one_each = []
    for i in range(len(dummy)):
        pokemon = dummy.iloc[i]
        if pd.isna(pokemon[others].unique()).all():
            one_each.append(i)
    return dummy[['No.','Caught?']+one].iloc[one_each].dropna()

def one_game_inclusive(one,others,dataframe):
    if type(one) == str:
        dummy = get_dif([one]+others,dataframe)
    else:
        dummy = get_dif(one+others,dataframe)
    one_each = []
    for i in range(len(dummy)):
        pokemon = dummy.iloc[i]
        if pd.isna(pokemon[others].unique()).all():
            one_each.append(i)
    indices = [list(dummy.index)[x] for x in one_each]
    # return dummy[['No.','Caught?']+one].iloc[one_each]
    return dataframe[['No.','Caught?']+one].loc[indices]

def main():
    # Initialize variables
    if 'df' not in st.session_state:
        df = pd.read_json("pokedex.json")
        df.index.name = 'Pokemon'
        df['Caught?'] = [False]*len(df)
        df = df[['No.','Caught?','Ruby','Sapphire','Leafgreen','Firered','Emerald','Colosseum','Xd']]
        st.session_state.df = df
        if 'caught' not in st.session_state:
            st.session_state.caught = st.session_state.df['Caught?']
    if 'mode' not in st.session_state:
        st.session_state.mode = 0

    #Define buttons and options
    games_list = ['Ruby','Sapphire','Leafgreen','Firered','Emerald','Colosseum','Xd']
    st.title('Gotta Catch \'Em All! Gen 3')
    # game = st.sidebar.selectbox("Game", options=games_list)
    button = st.sidebar.radio('Get Pokemon that are in',['all of','at least one of'])
    game = st.sidebar.multiselect(
        "",
        games_list,
        label_visibility='collapsed'
    )    
    game_not = st.sidebar.multiselect(
        "But not in:",
        games_list,
    )    

    uploaded_file = st.sidebar.file_uploader("Load a Previous Tracker")
    if uploaded_file is not None:
        try:
            st.session_state.df = pd.read_csv(uploaded_file,index_col="Pokemon")
            
        except:
            st.write("No list of Pokemon!")
    #Load Dataframe
    if game and game_not and button == 'all of':
        if st.session_state.mode != 1:
            st.session_state.df['Caught?'].loc[st.session_state.caught.index] = st.session_state.caught
            st.session_state.mode = 1
        st.text(f'Total Pokemon found: {len(one_game_exclusive(game,game_not,st.session_state.df))}')
        editor = st.data_editor(
            one_game_exclusive(game,game_not,st.session_state.df),
            column_config = {
                "Caught?":st.column_config.CheckboxColumn(
                None,
                help="Select which Pokemon you've already caught",
                width = "small",
                default=False,
                )
            },
            disabled=('Pokemon','No.',*game,*game_not)
        )
        st.session_state.caught = editor['Caught?']
        
    elif game and game_not and button == 'at least one of':
        if st.session_state.mode != 2:
            st.session_state.df['Caught?'].loc[st.session_state.caught.index] = st.session_state.caught
            st.session_state.mode = 2
        st.text(f'Total Pokemon found: {len(one_game_inclusive(game,game_not,st.session_state.df))}')
        editor = st.data_editor(
            one_game_inclusive(game,game_not,st.session_state.df),
            column_config = {
                "Caught?":st.column_config.CheckboxColumn(
                None,
                help="Select which Pokemon you've already caught",
                width = "small",
                default=False,
                )
            },
            disabled=('Pokemon','No.',*game,*game_not)
        )
        st.session_state.caught = editor['Caught?']
        
    elif game and button == 'all of':
        if st.session_state.mode != 3:
            st.session_state.df['Caught?'].loc[st.session_state.caught.index] = st.session_state.caught
            st.session_state.mode = 3
        st.text(f'Total Pokemon found: {len(get_intersection(game,st.session_state.df))}')
        editor = st.data_editor(
            get_intersection(game,st.session_state.df),
            column_config = {
                    "Caught?":st.column_config.CheckboxColumn(
                    None,
                    help="Select which Pokemon you've already caught",
                    width = "small",
                    default=False,
                )
            },
            disabled=('Pokemon','No.',*game)
           )
        st.session_state.caught = editor['Caught?']
        
    elif game and button == 'at least one of':
        if st.session_state.mode != 4:
            st.session_state.df['Caught?'].loc[st.session_state.caught.index] = st.session_state.caught
            st.session_state.mode = 4
        st.text(f'Total Pokemon found: {len(find_game(game,st.session_state.df))}')
        editor = st.data_editor(
            find_game(game,st.session_state.df),
            column_config = {
                "Caught?":st.column_config.CheckboxColumn(
                None,
                help="Select which Pokemon you've already caught",
                width = "small",
                default=False,
            )
        },
        disabled=('Pokemon','No.',*game)
       )
        st.session_state.caught = editor['Caught?']
        
    else:
        # st.write(st.session_state)
        if st.session_state.mode != 0:
            st.session_state.df['Caught?'].loc[st.session_state.caught.index] = st.session_state.caught
            st.session_state.mode = 0
        editor = st.data_editor(
            st.session_state.df,
            column_config = {
                    "Caught?":st.column_config.CheckboxColumn(
                    None,
                    help="Select which Pokemon you've already caught",
                    width = "small",
                    default=False,
                )
            },
            disabled=('Pokemon','No.',*games_list)
           )
        st.session_state.caught = editor['Caught?']
        
if __name__ == "__main__":
    main()