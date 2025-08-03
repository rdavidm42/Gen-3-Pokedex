import pandas as pd
import streamlit as st
import uuid
import re

st.set_page_config(layout="wide")

def find_game(column,dataframe):
    series = []
    for col in column:
        indices = [i for i in range(len(dataframe)) if dataframe[col].str.find('Trade from').iloc[i] == -1]
        series = series + indices
    series = list(set(series))
    return dataframe[['No.','Caught?',*column]].iloc[series]
    
def find_game_nan(column,dataframe):
    series = []
    for col in column:
        indices = [i for i in range(len(dataframe)) if dataframe[col].str.find('Trade from').iloc[i] == -1]
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

def searching(dataframe,columns,search_term):
    series = []
    for col in columns:
        indices = list(dataframe[col][dataframe[col].apply(
            lambda z: any(
                [all([bool(re.search('\D' + x + '\D',y.lower())) for x in search_term.lower().split()])
                 for y in re.split(r', (?=[A-Z])',' ' + z)]))].index)
        series = series + indices
    series = list(set(series))
    return dataframe[['No.','Caught?',*columns]].loc[series].sort_values(by='No.')

def update_value():
    """
    Located on top of the data editor.
    """
    st.session_state.df = pd.read_csv("pokedex.csv",index_col="Pokemon")
    st.session_state.dek = str(uuid.uuid4())  # triggers reset

def save_caught(): 
    st.session_state.df.loc[st.session_state.caught.index,'Caught?'] = st.session_state.caught

def main():
    
    # Initialize session_state variables
    
    if 'df' not in st.session_state:
        st.session_state.df = pd.read_csv("pokedex.csv",index_col="Pokemon")
    if 'caught' not in st.session_state:
        st.session_state.caught = st.session_state.df['Caught?']
    if 'file' not in st.session_state:
        st.session_state.file = True
    if 'search' not in st.session_state:
        st.session_state.search = False
    if 'dek' not in st.session_state:
        st.session_state.dek = str(uuid.uuid4())      
    if 'df_search' not in st.session_state:
        st.session_state.df_search = st.session_state.df

    #Define buttons and options
    games_list = ['Ruby','Sapphire','Leafgreen','Firered','Emerald','Colosseum','XD: Gale of Darkness']
    st.title('Gotta Catch \'Em All! Gen 3')
    with st.sidebar.form('search_form'):
        button = st.radio('Get Pokemon that are in',['all of','at least one of'])
        game = st.multiselect(
            "",
            games_list,
            label_visibility='collapsed'
        )    
        game_not = st.multiselect(
            "But not in:",
            games_list,
        )    
        search_bar = st.text_input('Keywords')
        
        st.form_submit_button("Search",on_click = save_caught)
        
    with st.sidebar:
        uploaded_file = st.file_uploader("Load a Previous Tracker")
        clear_button = st.button('Clear \"Caught?\" Column',on_click=update_value)

    #Get uploaded file, if available 
    if uploaded_file is not None and st.session_state.file:
        # try:
        update_value()
        st.session_state.df = pd.read_csv(uploaded_file,index_col="Pokemon")
        st.session_state.file = False
        st.rerun()
        # except:
            # st.write("No list of Pokemon!")
    elif uploaded_file is None:
        st.session_state.file = True

    #Load Dataframe based on options
    if game and game_not and button == 'all of':
        search_df = one_game_exclusive(game,game_not,st.session_state.df)
        
    elif game and game_not and button == 'at least one of':
        search_df = one_game_inclusive(game,game_not,st.session_state.df)
        
    elif game and button == 'all of':
        search_df = get_intersection(game,st.session_state.df)
        
    elif game and button == 'at least one of':
        search_df = find_game(game,st.session_state.df)
        
    else:
        search_df = st.session_state.df

    #Report back the dataframe
    
    if search_bar:
        if game:
            search_df = searching(search_df,game,search_bar)
        else:
            search_df = searching(search_df,games_list,search_bar)

    st.write(f'Total Pokemon found: {len(search_df)}')
    editor = st.data_editor(
        search_df,
        key = st.session_state.dek,
        column_config = {
                "Caught?":st.column_config.CheckboxColumn(
                None,
                help="Select which Pokemon you've already caught",
                default=False,
            )
        },
        disabled = ('Pokemon','No.',*games_list)       
    )
    
    #Record the changes to the dataframe
    # st.session_state.caught = editor.iloc[list(st.session_state[st.session_state.dek]["edited_rows"].keys())]['Caught?']
    # st.session_state.caught = pd.DataFrame.from_dict(
    #     st.session_state[st.session_state.dek]["edited_rows"],orient='index').set_index(
    #     editor.index[list(st.session_state[st.session_state.dek]["edited_rows"].keys())])
    st.session_state.caught = pd.Series(
        [x['Caught?'] for x in list(st.session_state[st.session_state.dek]["edited_rows"].values())],
        index=editor.index[list(st.session_state[st.session_state.dek]["edited_rows"].keys())])
if __name__ == "__main__":
    main()