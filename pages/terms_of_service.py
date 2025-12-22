"""
Terms of Service Page
Official Terms of Service for REImagineHome Content Creator
"""

import streamlit as st

def show():
    st.title("📜 Terms of Service")
    st.caption("Last Updated: December 22, 2024")
    
    st.markdown("---")
    
    st.markdown("""
    ## 1. Acceptance of Terms
    
    By accessing and using REImagineHome Content Creator ("the Service"), you accept and agree to be bound by the terms and provisions of this agreement. If you do not agree to abide by these terms, please do not use this Service.
    
    ---
    
    ## 2. Description of Service
    
    REImagineHome Content Creator is a content management platform that enables users to:
    
    - Create, edit, and manage video content
    - Generate AI-powered scripts for video productions
    - Publish content to multiple social media platforms including YouTube, Instagram, TikTok, and Facebook
    - Manage and schedule content distribution
    
    ---
    
    ## 3. User Accounts
    
    ### 3.1 Account Creation
    To use certain features of the Service, you must create an account. You agree to:
    - Provide accurate and complete information
    - Maintain the security of your account credentials
    - Promptly update any information to keep it accurate
    - Accept responsibility for all activities under your account
    
    ### 3.2 Account Security
    You are responsible for safeguarding your password and for any activities or actions under your account. You must notify us immediately of any unauthorized use of your account.
    
    ---
    
    ## 4. User Content
    
    ### 4.1 Ownership
    You retain ownership of any content you create, upload, or publish through the Service ("User Content"). By using the Service, you grant us a limited license to process your content solely for the purpose of providing the Service.
    
    ### 4.2 User Responsibilities
    You are solely responsible for:
    - The content you create and publish
    - Ensuring your content does not violate any laws or third-party rights
    - Obtaining necessary permissions for any content you upload
    - Compliance with platform-specific terms of service (YouTube, TikTok, Instagram, Facebook)
    
    ### 4.3 Prohibited Content
    You agree not to use the Service to create or distribute content that:
    - Is illegal, harmful, threatening, abusive, or defamatory
    - Infringes on intellectual property rights
    - Contains malware or harmful code
    - Violates privacy rights of others
    - Is spam or misleading
    - Violates any applicable laws or regulations
    
    ---
    
    ## 5. Third-Party Services
    
    ### 5.1 Social Media Platforms
    The Service integrates with third-party platforms including:
    - YouTube (Google)
    - TikTok
    - Instagram (Meta)
    - Facebook (Meta)
    
    Your use of these platforms through our Service is also subject to their respective terms of service and policies.
    
    ### 5.2 API Usage
    We use official APIs provided by these platforms. By connecting your social media accounts, you authorize us to:
    - Access account information necessary for posting content
    - Upload and publish content on your behalf
    - Retrieve engagement metrics and analytics
    
    ---
    
    ## 6. AI-Generated Content
    
    ### 6.1 Script Generation
    The Service uses OpenAI's API to generate video scripts. You understand that:
    - AI-generated content is provided "as-is"
    - You are responsible for reviewing and editing generated content
    - Generated content may require fact-checking before publication
    - AI output should comply with your content guidelines
    
    ### 6.2 Usage Rights
    You may use AI-generated scripts for your personal or commercial purposes, subject to OpenAI's usage policies.
    
    ---
    
    ## 7. Intellectual Property
    
    ### 7.1 Service Ownership
    The Service, including its original content, features, and functionality, is owned by REImagineHome and is protected by international copyright, trademark, and other intellectual property laws.
    
    ### 7.2 Trademarks
    Our trademarks and trade dress may not be used in connection with any product or service without prior written consent.
    
    ---
    
    ## 8. Payment Terms
    
    ### 8.1 Fees
    Certain features of the Service may require payment. All fees are:
    - Quoted in USD unless otherwise specified
    - Non-refundable unless otherwise stated
    - Subject to change with reasonable notice
    
    ### 8.2 Third-Party Costs
    You are responsible for any costs associated with:
    - API usage fees (OpenAI, cloud storage, etc.)
    - Social media platform advertising fees
    - Internet connectivity and hardware
    
    ---
    
    ## 9. Limitation of Liability
    
    ### 9.1 Disclaimer
    THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED.
    
    ### 9.2 Limitation
    TO THE MAXIMUM EXTENT PERMITTED BY LAW, REIMAGINEHOME SHALL NOT BE LIABLE FOR:
    - Any indirect, incidental, special, consequential, or punitive damages
    - Loss of profits, data, use, goodwill, or other intangible losses
    - Content published to third-party platforms
    - Actions taken by third-party platforms
    - Service interruptions or failures
    
    ---
    
    ## 10. Indemnification
    
    You agree to defend, indemnify, and hold harmless REImagineHome and its affiliates from any claims, damages, losses, and expenses arising from:
    - Your use of the Service
    - Your User Content
    - Your violation of these Terms
    - Your violation of any third-party rights
    
    ---
    
    ## 11. Termination
    
    ### 11.1 By You
    You may terminate your account at any time by discontinuing use of the Service and deleting your account.
    
    ### 11.2 By Us
    We reserve the right to suspend or terminate your access to the Service at any time, with or without cause, with or without notice.
    
    ### 11.3 Effect of Termination
    Upon termination:
    - Your right to use the Service will immediately cease
    - We may delete your account and associated data
    - Provisions that should survive will remain in effect
    
    ---
    
    ## 12. Changes to Terms
    
    We reserve the right to modify these Terms at any time. We will notify users of significant changes via:
    - Email notification
    - In-app notification
    - Website announcement
    
    Continued use of the Service after changes constitutes acceptance of the modified Terms.
    
    ---
    
    ## 13. Governing Law
    
    These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict of law provisions.
    
    ---
    
    ## 14. Dispute Resolution
    
    Any disputes arising from these Terms or the Service shall be resolved through:
    1. Good faith negotiation
    2. Mediation if negotiation fails
    3. Binding arbitration as a last resort
    
    ---
    
    ## 15. Contact Information
    
    For questions about these Terms of Service, please contact us at:
    
    **REImagineHome**
    - Email: support@reimaginehome.ai
    - Website: https://reimaginehome.ai
    
    ---
    
    ## 16. Severability
    
    If any provision of these Terms is found to be unenforceable, the remaining provisions will continue in full force and effect.
    
    ---
    
    ## 17. Entire Agreement
    
    These Terms constitute the entire agreement between you and REImagineHome regarding the Service and supersede any prior agreements.
    
    ---
    
    *By using REImagineHome Content Creator, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.*
    """)
    
    st.markdown("---")
    
    # Back button
    if st.button("← Back to App"):
        st.switch_page("app.py")

if __name__ == "__main__":
    show()
