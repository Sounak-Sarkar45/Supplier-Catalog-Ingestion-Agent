import json
import base64
import mysql.connector
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from config import (
    GraphState, llm_extraction, llm_email, 
    MYSQL_CONFIG, SMTP_CONFIG, NEW_CATALOG_ITEM_TEMPLATE
)

# Node Functions

def node_extract_data(state: GraphState) -> GraphState:
    """Step 1: Extract fields from image using a multimodal LLM."""
    print("--- 🚀 Node: Extracting Data from Image ---")
    
    encoded_image = state["encoded_image"]
    template = state["extraction_template"]
    
    system_prompt = "You are a precise document extraction assistant. Respond strictly as a JSON object."
    user_prompt = f"""
    Extract the fields from the supplier catalog image and return ONLY valid JSON.
    Do not include any explanations, comments, or code block formatting (no backticks).
    
    Respond strictly as a JSON object with the following structure:
    
    {json.dumps(template, indent=4)}
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=[
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
            ]
        ),
    ]

    response = llm_extraction.invoke(messages)
    
    extracted_data = {}
    new_catalog_item = template.copy()
    
    try:
        # Robust JSON parsing
        content = response.content.strip()
        if content.startswith("```"): content = content.strip("`").strip("json").strip()
             
        extracted_data = json.loads(content)
        new_catalog_item.update(extracted_data)
        print("✅ Data Extraction Successful.")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON from LLM. Error: {e}")
        new_catalog_item['Extraction_Confidence'] = 0.0

    # Data Type Cleanup
    for key in ['Price', 'MOQ']:
        value = new_catalog_item.get(key)
        if isinstance(value, str):
            try:
                new_catalog_item[key] = float(value.replace('$', '').replace(',', '').strip())
            except ValueError:
                new_catalog_item[key] = None

    return {"extracted_item": new_catalog_item}

def node_fetch_historical_data(state: GraphState) -> GraphState:
    """Step 2: Fetch historical data from MySQL (or use dummy data on failure)."""
    print("\n--- 💾 Node: Fetching Historical Data ---")
    df_input_historical = pd.DataFrame()
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        table_name = "supplier_catalog_agent_dataset"
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df_input_historical = pd.DataFrame(rows, columns=columns)
        print("✅ Historical Data Fetch Successful.")
    except Exception as e:
        print(f"⚠️ Could not fetch data from MySQL. Using dummy data. Error: {e}")
        df_input_historical = pd.DataFrame({
            'Product Name': ['Face-to-face encompassing protocol']*2 + ['Triple-buffered asynchronous model']*2,
            'SKU': ['SKU-1207', 'SKU-9990', 'SKU-8888', 'SKU-7777'],
            'Price': [33.52, 245.3, 240.5, 250.1],
            'Category': ['Electronics', 'Hardware', 'Hardware', 'Hardware'],
            'Supplier': ['Aperture', 'Black Mesa', 'Black Mesa', 'Aperture']
        })

    return {"historical_df": df_input_historical}

def node_run_agent_validation(state: GraphState) -> GraphState:
    """Steps 3 & 4: Apply business rules, add tags, and determine final status."""
    print("\n--- ⚙️ Node: Running Agent Validation ---")
    item = state["extracted_item"]
    historical_data = state["historical_df"]
    
    product_name = item.get('Product Name', 'value not provided')
    price = item.get('Price')
    moq = item.get('MOQ')
    availability = item.get('Availability', 'value not provided')
    extraction_confidence = item.get('Extraction_Confidence', 1.0)
    
    factors = []

    if isinstance(moq, (int, float)) and moq >= 100:
        factors.append("MOQ Discrepancy")

    deviation_threshold_percent = 5
    if isinstance(price, (int, float)) and isinstance(product_name, str):
        product_df = historical_data[historical_data['Product Name'] == product_name]
        if not product_df.empty:
            numeric_prices = pd.to_numeric(product_df['Price'], errors='coerce').dropna()
            
            if not numeric_prices.empty:
                mean_old_price = numeric_prices.mean()
                deviation = abs(price - mean_old_price) / mean_old_price * 100
                if deviation > deviation_threshold_percent:
                    factors.append("Price Out of Range")

    if isinstance(availability, str) and availability.lower() == 'discontinued':
        factors.append("Discontinued Model")

    if extraction_confidence < 0.85:
        factors.append("Low Confidence Extraction")

    if not factors:
        final_factors = "Validated"
        suggested_status = "Validated"
    else:
        final_factors = ", ".join(factors)
        suggested_status = "Pending Review"

    date_field = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_result = {
        "Date": date_field,
        "Product_Name": product_name,
        "SKU": item.get('SKU', 'value not provided'),
        "Price": price,
        "MOQ": moq,
        "Availability": availability,
        "Suggested_Factors": final_factors,
        "Suggested_Status": suggested_status
    }

    for k, v in final_result.items():
        if v is None:
            final_result[k] = 'value not provided'

    print(f"✅ Validation Complete. Status: {suggested_status} | Factors: {final_factors}")
    return {
        "final_result": final_result,
        "factors": factors,
        "suggested_status": suggested_status
    }

def node_prepare_and_insert_db(state: GraphState) -> GraphState:
    """Step 5 (Part 2): Format data and insert the final result into MySQL."""
    print("\n--- 💿 Node: Preparing Data and Inserting into DB ---")
    final_result = state["final_result"]
    historical_data = state["historical_df"]
    extracted_item = state["extracted_item"]

    price_value = final_result.get("Price")
    price_formatted = f"${price_value:.2f}" if isinstance(price_value, (int, float)) else final_result.get("Price", "value not provided")
    
    date_value = final_result.get("Date", "value not provided")
    date_formatted = date_value 
    try:
        dt_obj = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
        hour = dt_obj.hour % 12 or 12
        am_pm = "AM" if dt_obj.hour < 12 else "PM"
        date_formatted = f"{dt_obj.month}/{dt_obj.day}/{dt_obj.year}, {hour}:{dt_obj.minute:02d}:{dt_obj.second:02d} {am_pm} UTC"
    except:
        pass

    matched_row = historical_data[
        (historical_data['SKU'] == final_result.get("SKU")) |
        (historical_data['Product Name'] == final_result.get("Product_Name"))
    ]
    
    category_value = matched_row.iloc[0].get("Category", "value not provided") if not matched_row.empty and 'Category' in matched_row.columns else "value not provided"
    supplier_value = matched_row.iloc[0].get("Supplier", "value not provided") if not matched_row.empty and 'Supplier' in matched_row.columns else "value not provided"

    row_data = {
        "Date": date_formatted,
        "Product_Name": final_result.get("Product_Name", "value not provided"),
        "SKU": final_result.get("SKU", "value not provided"),
        "Description": extracted_item.get("Description", "value not provided"),
        "Category": category_value,
        "Price": price_formatted,
        "MOQ": final_result.get("MOQ", "value not provided"),
        "Specification": extracted_item.get("Specifications", "value not provided"),
        "Availability_Status": final_result.get("Availability", "value not provided"),
        "Supplier": supplier_value,
        "Phone": extracted_item.get("Phone", "value not provided"), 
        "Mail": extracted_item.get("Mail", "value not provided"),   
        "Suggested_Description": final_result.get("Suggested_Factors", "value not provided"),
        "Status": final_result.get("Suggested_Status", "value not provided")
    }

    conn, cursor = None, None
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        table_name = "supplier_catalog_details"
        columns = ", ".join(row_data.keys())
        placeholders = ", ".join(["%s"] * len(row_data))
        values = tuple(row_data.values())
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(insert_query, values)
        conn.commit()
        print(f"✅ Database table '{table_name}' updated successfully.")
    except mysql.connector.Error as err:
        print(f"❌ Error inserting into DB: {err}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return {"row_data_for_db": row_data}

def node_generate_email_content(state: GraphState) -> GraphState:
    """Step 6 (Part 1): Generate the HTML email body and subject using LLMs."""
    print("\n--- 📧 Node: Generating Email Content ---")
    row_data = state["row_data_for_db"]

    rules_explanation = """
    Business Rules for Discrepancies:
    1. MOQ Discrepancy → Triggered when the Minimum Order Quantity (MOQ) is >= 100.
    2. Price Out of Range → Triggered when the current price deviates >5% from historical mean.
    3. Discontinued Model → Triggered when availability status is 'Discontinued'.
    """
    
    prompt_text = f"""
    You are an assistant drafting a professional email in HTML format for a Procurement Manager.
    Use a neutral, report-style tone. Include a brief introduction, a structured summary in a table,
    discrepancies flagged in a bullet list, reasons for flags based on rules, and recommended follow-up actions.
    
    Do not include any subject line or first-person language.
    
    Business rules:
    {rules_explanation}
    
    Product ingestion data:
    Date: {row_data['Date']}
    Product Name: {row_data['Product_Name']}
    SKU: {row_data['SKU']}
    Description: {row_data['Description']}
    Category: {row_data['Category']}
    Price: {row_data['Price']}
    MOQ: {row_data['MOQ']}
    Specification: {row_data['Specification']}
    Availability Status: {row_data['Availability_Status']}
    Supplier: {row_data['Supplier']}
    Phone: {row_data['Phone']}
    Mail: {row_data['Mail']}
    Suggested Description (Flags): {row_data['Suggested_Description']}
    Status: {row_data['Status']}
    """

    response_body = llm_email.invoke([HumanMessage(content=prompt_text)])
    email_body_html = response_body.content

    subject_prompt = f"""
    Generate a brief, professional email subject (≤12 words) for:
    Product Name: {row_data['Product_Name']}
    SKU: {row_data['SKU']}
    Status Flags: {row_data['Status']}
    Date: {row_data['Date']}
    """
    subject_response = llm_email.invoke([HumanMessage(content=subject_prompt)])
    email_subject = subject_response.content.strip()

    print(f"✅ Email Content Generated. Subject: {email_subject}")
    return {
        "email_subject": email_subject,
        "email_body_html": email_body_html
    }

def node_send_email(state: GraphState) -> GraphState:
    """Step 6 (Part 2): Send the generated HTML email via SMTP."""
    print("\n--- 📤 Node: Sending Email ---")
    email_subject = state["email_subject"]
    email_body_html = state["email_body_html"]

    msg = MIMEMultipart()
    msg["From"] = SMTP_CONFIG["SENDER_EMAIL"]
    msg["To"] = SMTP_CONFIG["RECEIVER_EMAIL"]
    msg["Subject"] = email_subject
    msg.attach(MIMEText(email_body_html, "html"))

    try:
        server = smtplib.SMTP_SSL(SMTP_CONFIG["SMTP_SERVER"], SMTP_CONFIG["SMTP_PORT"])
        server.login(SMTP_CONFIG["SENDER_EMAIL"], SMTP_CONFIG["SENDER_PASSWORD"])
        server.sendmail(SMTP_CONFIG["SENDER_EMAIL"], SMTP_CONFIG["RECEIVER_EMAIL"], msg.as_string())
        server.quit()
        print("✅ HTML Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        
    return {}

# Graph Compilation

def compile_agent_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(GraphState)
    
    workflow.add_node("extract_data", node_extract_data)
    workflow.add_node("fetch_historical_data", node_fetch_historical_data)
    workflow.add_node("run_agent_validation", node_run_agent_validation)
    workflow.add_node("prepare_and_insert_db", node_prepare_and_insert_db)
    workflow.add_node("generate_email_content", node_generate_email_content)
    workflow.add_node("send_email", node_send_email)
    
    workflow.set_entry_point("extract_data")
    workflow.add_edge("extract_data", "fetch_historical_data")
    workflow.add_edge("fetch_historical_data", "run_agent_validation")
    workflow.add_edge("run_agent_validation", "prepare_and_insert_db")
    workflow.add_edge("prepare_and_insert_db", "generate_email_content")
    workflow.add_edge("generate_email_content", "send_email")
    workflow.add_edge("send_email", END)
    
    return workflow.compile()

# Compile the graph globally for the FastAPI app to import
AGENT_APP = compile_agent_graph()