# Import Python packages
import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Connect to Snowflake using Streamlit Secrets
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit names and the values used by the API
my_dataframe = (
    session
    .table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )
)

# Convert the Snowpark DataFrame to a Pandas DataFrame
pd_df = my_dataframe.to_pandas()

# Uncomment these lines only to inspect the DataFrame
# st.dataframe(pd_df, use_container_width=True)
# st.stop()

fruit_options = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options,
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list)

    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write(
            "The search value for",
            fruit_chosen,
            "is",
            search_on,
            "."
        )

        st.subheader(f"{fruit_chosen} Nutrition Information")

        try:
            smoothiefroot_response = requests.get(
                f"https://my.smoothiefroot.com/api/fruit/{search_on}",
                timeout=10
            )

            smoothiefroot_response.raise_for_status()

            st.dataframe(
                smoothiefroot_response.json(),
                use_container_width=True
            )

        except requests.RequestException as error:
            st.error(
                f"Unable to retrieve nutrition information for {fruit_chosen}."
            )
            st.write(error)

    time_to_insert = st.button("Submit Order")

    if time_to_insert:
        if not name_on_order.strip():
            st.warning("Please enter a name for the order.")
        else:
            insert_stmt = """
                INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                    (INGREDIENTS, NAME_ON_ORDER)
                VALUES (?, ?)
            """

            session.sql(
                insert_stmt,
                params=[ingredients_string, name_on_order.strip()]
            ).collect()

            st.success(
                f"Your Smoothie is ordered, {name_on_order.strip()}!",
                icon="✅"
            )
