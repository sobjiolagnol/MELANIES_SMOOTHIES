# Import Python packages
import pandas as pd
import requests
import streamlit as st
from snowflake.snowpark.functions import col

# Page content
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

# Get fruit names and the search values used by the API
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

fruit_options = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options,
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list)

    for fruit_chosen in ingredients_list:
        matching_rows = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ]

        st.subheader(f"{fruit_chosen} Nutrition Information")

        if matching_rows.empty:
            st.info(
                f"Nutrition information is not available for {fruit_chosen}."
            )
            continue

        search_on = matching_rows.iloc[0]

        # Do not call the API when SEARCH_ON is NULL or empty
        if pd.isna(search_on) or not str(search_on).strip():
            st.info(
                f"Nutrition information is not available for {fruit_chosen}."
            )
            continue

        search_on = str(search_on).strip()

        st.write(
            "The search value for",
            fruit_chosen,
            "is",
            search_on,
            "."
        )

        try:
            smoothiefroot_response = requests.get(
                f"https://my.smoothiefroot.com/api/fruit/{search_on}",
                timeout=10
            )

            if smoothiefroot_response.status_code == 404:
                st.info(
                    f"Nutrition information is not available for {fruit_chosen}."
                )
                continue

            smoothiefroot_response.raise_for_status()

            nutrition_data = smoothiefroot_response.json()

            st.dataframe(
                nutrition_data,
                use_container_width=True
            )

        except requests.exceptions.Timeout:
            st.warning(
                f"The nutrition service took too long to respond for {fruit_chosen}."
            )

        except requests.exceptions.RequestException:
            st.warning(
                f"Unable to retrieve nutrition information for {fruit_chosen}."
            )

        except ValueError:
            st.warning(
                f"The nutrition service returned invalid data for {fruit_chosen}."
            )

    if st.button("Submit Order"):
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
                params=[
                    ingredients_string,
                    name_on_order.strip()
                ]
            ).collect()

            st.success(
                f"Your Smoothie is ordered, {name_on_order.strip()}!",
                icon="✅"
            )
