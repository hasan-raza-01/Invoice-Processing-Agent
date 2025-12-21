"""Streamlit Human Review Dashboard"""
import streamlit as st
import requests
import os
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Invoice Review Dashboard",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Invoice Processing - Human Review Dashboard")
st.markdown("---")

# Sidebar info
with st.sidebar:
    st.header("ℹ️ System Info")
    st.info(f"**API Endpoint**: {API_URL}")
    st.success("**Status**: Online")
    
    if st.button("🔄 Refresh Reviews"):
        st.rerun()

# Fetch pending reviews
try:
    response = requests.get(f"{API_URL}/human-review/pending")
    
    if response.status_code == 200:
        data = response.json()
        reviews = data.get("items", [])
        
        if not reviews:
            st.success("✅ No pending reviews! All invoices processed.")
            st.balloons()
        else:
            st.warning(f"⚠️ **{len(reviews)} invoices** awaiting human review")
            st.markdown("---")
            
            # Display each review
            for idx, review in enumerate(reviews):
                with st.expander(
                    f"📄 Invoice {review['invoice_id']} - {review['vendor_name']} - ${review['amount']:.2f}",
                    expanded=(idx == 0)  # Expand first item by default
                ):
                    # Display review details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Vendor**: {review['vendor_name']}")
                        st.markdown(f"**Invoice ID**: {review['invoice_id']}")
                        st.markdown(f"**Amount**: ${review['amount']:.2f}")
                    
                    with col2:
                        st.markdown(f"**Checkpoint ID**: `{review['checkpoint_id']}`")
                        st.markdown(f"**Created**: {review.get('created_at', 'N/A')}")
                    
                    st.markdown(f"**Reason for Hold**: {review['reason_for_hold']}")
                    
                    st.markdown("---")
                    
                    # Decision buttons
                    col3, col4, col5 = st.columns([1, 1, 3])
                    
                    with col3:
                        if st.button("✅ Accept", key=f"accept_{review['checkpoint_id']}", type="primary"):
                            # Submit ACCEPT decision
                            try:
                                decision_response = requests.post(
                                    f"{API_URL}/human-review/decision",
                                    json={
                                        "checkpoint_id": review["checkpoint_id"],
                                        "decision": "ACCEPT",
                                        "notes": "Approved by reviewer",
                                        "reviewer_id": "reviewer_001"
                                    }
                                )
                                
                                if decision_response.status_code == 200:
                                    st.success("✅ Invoice ACCEPTED! Workflow resuming...")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"Error: {decision_response.text}")
                            except Exception as e:
                                st.error(f"Failed to submit decision: {e}")
                    
                    with col4:
                        if st.button("❌ Reject", key=f"reject_{review['checkpoint_id']}", type="secondary"):
                            # Submit REJECT decision
                            try:
                                decision_response = requests.post(
                                    f"{API_URL}/human-review/decision",
                                    json={
                                        "checkpoint_id": review["checkpoint_id"],
                                        "decision": "REJECT",
                                        "notes": "Rejected by reviewer",
                                        "reviewer_id": "reviewer_001"
                                    }
                                )
                                
                                if decision_response.status_code == 200:
                                    st.warning("❌ Invoice REJECTED. Manual handling required.")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {decision_response.text}")
                            except Exception as e:
                                st.error(f"Failed to submit decision: {e}")
    else:
        st.error(f"Failed to fetch reviews: {response.status_code}")
        st.code(response.text)
        
except requests.exceptions.ConnectionError:
    st.error("🔴 Cannot connect to API server!")
    st.info(f"Please ensure the API is running at: {API_URL}")
except Exception as e:
    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("Invoice Processing Agent - LangGraph with HITL Checkpoints")
