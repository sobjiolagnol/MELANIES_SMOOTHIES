# Import Python packages
import streamlit as st
import requests  
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




# Get the available fruit names
fruit_rows = (
    session
    .table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"))
    .collect()
)

fruit_options = [row["FRUIT_NAME"] for row in fruit_rows]

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options,
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list)

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


if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ''
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)






