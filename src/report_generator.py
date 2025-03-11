import pandas as pd
import yaml
from reportlab.platypus.tables import TableStyle
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Image
from reportlab.platypus.flowables import PageBreak, Spacer, Flowable, KeepTogether
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PyPDF2 import PdfReader, PdfWriter
import pdfkit
import io
import re
import datetime
from datetime import datetime
import os
import tempfile
import logging
import math
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import simpleSplit
import numpy as np
import subprocess
from io import BytesIO
from reportlab.lib.pagesizes import A4

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom TableOfContents class
class CustomTOC(Flowable):
    """
    A custom Table of Contents flowable for ReportLab.
    """
    def __init__(self, bookmarks=None, levelStyles=None):
        Flowable.__init__(self)
        self.bookmarks = bookmarks or []
        self.levelStyles = levelStyles or []
        self.width = 0
        self.height = 0
        
    def wrap(self, availWidth, availHeight):
        """
        Determine the dimensions of the TOC.
        """
        self.width = availWidth
        self.height = availHeight
        return (self.width, self.height)
        
    def draw(self):
        """
        Draw the TOC on the canvas.
        """
        # This is a placeholder - the actual TOC is built separately
        pass

class ReportEngine:
    def __init__(self, config, scenarios, db_cursor, env="qa"):
        """Initialize the report engine with configuration."""
        self.config = config
        self.scenarios = scenarios
        self.db_cursor = db_cursor
        self.env = env
        self.reports = config.get("reports", {})
        
        # Set up page size and margins
        self.page_size = landscape(A4)
        self.page_width, self.page_height = self.page_size
        self.left_margin = inch * 0.5
        self.right_margin = inch * 0.5
        self.top_margin = inch * 0.5
        self.bottom_margin = inch * 0.5
        
        # Set up document metadata
        self.title = self.reports.get("title", "Risk Oversight Report")
        self.author = self.reports.get("author", "Risk Management")
        self.subject = self.reports.get("subject", "Risk Analysis")
        self.creator = self.reports.get("creator", "Report Engine")
        self.producer = self.reports.get("producer", "ReportLab")
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
        # Flag manager for data processing
        self.flag_manager = FlagManager(config.get("flag_rules", []))
        
        # Initialize wkhtmltopdf path
        self.wkhtmltopdf_path = config.get("wkhtmltopdf_path", None)
        
        # Initialize Jinja2 environment for templates
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Register custom filters
        self.jinja_env.filters['format_date'] = self._format_date
        self.jinja_env.filters['format_number'] = self._format_number
        
        try:
            # Validate required configuration
            if not isinstance(config, dict):
                raise ValueError("Config must be a dictionary")
            
            self.common = self.config.get("common", {})
            
            # Validate required config sections
            if not self.reports:
                raise ValueError("Missing 'reports' section in configuration")
            
            self.bookmarks = []  # Initialize bookmarks list for TOC
            self.current_page_number = 1  # Track current page number
            self.toc_page_numbers = {}  # Dictionary to store section titles and their page numbers
            self.mapping_dict = {}
            
            # Initialize previous business line and sub team name
            self.previous_business_line = None
            self.previous_sub_team_name = None
            
            # Customize text styles if needed
            self.levelStyles = [
                ParagraphStyle(fontName="Helvetica-Bold", fontSize=12, name="TOCHeading1Level1",
                              spaceBefore=6, leading=16),
                ParagraphStyle(fontName="Helvetica", fontSize=10, name="TOCHeading1Level2",
                              leftIndent=20, spaceBefore=4, leading=14)
            ]
            
            # Set up styles
            self._setup_styles()
            
        except Exception as e:
            logger.error(f"Error initializing ReportEngine: {str(e)}")
            raise

    def _setup_styles(self):
        """Set up document styles."""
        # Add styles for TOC if they don't exist
        if 'TOCTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name="TOCTitle", 
                fontSize=16, 
                leading=20, 
                spaceBefore=20, 
                spaceAfter=10, 
                alignment=TA_CENTER
            ))
        
        if 'TOCHeading1' not in self.styles:
            self.styles.add(ParagraphStyle(
                name="TOCHeading1", 
                fontSize=12, 
                leading=14, 
                spaceBefore=6, 
                spaceAfter=6, 
                leftIndent=20, 
                firstLineIndent=-20
            ))
        
        if 'TOCHeading2' not in self.styles:
            self.styles.add(ParagraphStyle(
                name="TOCHeading2", 
                fontSize=10, 
                leading=12, 
                spaceBefore=4, 
                spaceAfter=4, 
                leftIndent=40, 
                firstLineIndent=-20
            ))
        
        # Add styles for headings if they don't exist
        if 'Heading1' not in self.styles:
            self.styles.add(ParagraphStyle(
                name="Heading1", 
                fontSize=16, 
                leading=20, 
                spaceBefore=12, 
                spaceAfter=6, 
                alignment=TA_LEFT
            ))
        
        if 'Heading2' not in self.styles:
            self.styles.add(ParagraphStyle(
                name="Heading2", 
                fontSize=14, 
                leading=18, 
                spaceBefore=10, 
                spaceAfter=4, 
                alignment=TA_LEFT
            ))
        
        # Add styles for body text if they don't exist
        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name="BodyText", 
                fontSize=10, 
                leading=14, 
                spaceBefore=6, 
                spaceAfter=6, 
                alignment=TA_LEFT
            ))

    def render_front_page(self, effective_date):
        """ Render the first page using Jinja2 and convert it to PDF. """
        try:
            # Create templates directory if it doesn't exist
            templates_dir = "./templates"
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            env = Environment(loader=FileSystemLoader(templates_dir))
            try:
                template = env.get_template("front_page.html")
            except Exception as e:
                logger.error(f"Error loading front page template: {str(e)}")
                # Create a simple front page using ReportLab as fallback
                return self._create_fallback_front_page(effective_date)
            
            if isinstance(effective_date, str):
                effective_date = datetime.strptime(effective_date, "%Y-%m-%d").strftime("%B %d, %Y")
            
            # Validate front page config
            front_page_config = self.config.get('front_page', {})
            if not front_page_config:
                logger.warning("Missing front page configuration, using defaults")
                front_page_config = {
                    "title": "Report",
                    "subtitle": ""
                }
            
            html_content = template.render({
                "config": front_page_config,
                "effective_date": effective_date
            })
            
            # Use a temporary file with proper cleanup
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
                temp_file.write(html_content)
                temp_file_name = temp_file.name
            
            try:
                # Try to convert HTML to PDF using pdfkit
                pdf_content = pdfkit.from_file(temp_file_name, False)
                return pdf_content
            except Exception as e:
                logger.error(f"Error converting HTML to PDF with pdfkit: {str(e)}")
                logger.info("Falling back to ReportLab for front page generation")
                return self._create_fallback_front_page(effective_date)
            
        except Exception as e:
            logger.error(f"Error rendering front page: {str(e)}")
            # Create a simple front page using ReportLab as fallback
            return self._create_fallback_front_page(effective_date)
        finally:
            # Clean up temporary file
            if 'temp_file_name' in locals() and os.path.exists(temp_file_name):
                try:
                    os.remove(temp_file_name)
                except Exception as e:
                    logger.warning(f"Error cleaning up temporary file: {str(e)}")
    
    def _create_fallback_front_page(self, effective_date):
        """Create a simple front page using ReportLab when wkhtmltopdf is not available."""
        buffer = io.BytesIO()
        
        # Format the date if it's a string
        if isinstance(effective_date, str):
            try:
                formatted_date = datetime.strptime(effective_date, "%Y-%m-%d").strftime("%B %d, %Y")
            except:
                formatted_date = effective_date
        else:
            formatted_date = effective_date.strftime("%B %d, %Y")
        
        # Get front page config
        front_page_config = self.config.get('front_page', {})
        title = front_page_config.get('title', 'Report')
        subtitle = front_page_config.get('subtitle', '')
        company_name = front_page_config.get('company_name', '')
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            leftMargin=72, 
            rightMargin=72,
            topMargin=72, 
            bottomMargin=72
        )
        
        # Create elements for the front page
        elements = []
        
        # Add title
        title_style = ParagraphStyle(
            name='Title',
            fontName='Helvetica-Bold',
            fontSize=24,
            alignment=1,  # Center alignment
            spaceAfter=30
        )
        elements.append(Paragraph(title, title_style))
        
        # Add subtitle
        if subtitle:
            subtitle_style = ParagraphStyle(
                name='Subtitle',
                fontName='Helvetica',
                fontSize=18,
                alignment=1,
                spaceAfter=40
            )
            elements.append(Paragraph(subtitle, subtitle_style))
        
        # Add company name
        if company_name:
            company_style = ParagraphStyle(
                name='Company',
                fontName='Helvetica-Bold',
                fontSize=16,
                alignment=1,
                spaceAfter=60
            )
            elements.append(Paragraph(company_name, company_style))
        
        # Add effective date
        date_style = ParagraphStyle(
            name='Date',
            fontName='Helvetica',
            fontSize=14,
            alignment=1,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Effective Date: {formatted_date}", date_style))
        
        # Add confidential marking
        confidential_style = ParagraphStyle(
            name='Confidential',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=1,
            textColor=colors.red,
            spaceAfter=40
        )
        elements.append(Paragraph("CONFIDENTIAL", confidential_style))
        
        # Build the document
        doc.build(elements)
        
        # Get the PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content

    def generate_report_pages(self):
        """ Generate report pages using ReportLab. """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = [Paragraph("This is the main body of the report.", self.styles["BodyText"]), PageBreak()]
        doc.build(elements)
        return buffer.getvalue()

    def combine_pdfs(self, pdf_front, pdf_report):
        """ Combine front page and report PDFs with proper error handling. """
        try:
            if not isinstance(pdf_front, bytes):
                raise ValueError("pdf_front must be of type bytes")
            
            output_pdf = PdfWriter()
            front_pdf_reader = PdfReader(io.BytesIO(pdf_front))
            report_pdf_reader = PdfReader(io.BytesIO(pdf_report))
            
            # Add the front page
            output_pdf.add_page(front_pdf_reader.pages[0])
            
            # Add remaining report pages
            for page in report_pdf_reader.pages:
                output_pdf.add_page(page)
            
            # Use a temporary file for the combined PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                output_pdf.write(temp_file)
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Error combining PDFs: {str(e)}")
            raise

    def run_report(self):
        effective_date = self.common.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
        pdf_front = self.render_front_page(effective_date)
        pdf_report = self.generate_report_pages()
        self.combine_pdfs(pdf_front, pdf_report)

    def get_flagged_style(self, bg_color, text_color):
        return ParagraphStyle(
            name="FlaggedStyle",
            backColor=bg_color,
            textColor=text_color,
            fontName="Helvetica-Bold",
            fontSize=7
        )

    def get_custom_style(self):
        styles = getSampleStyleSheet()
        custom_style = styles["BodyText"]
        custom_style.wordwrap = "CJK"
        custom_style.fontSize = 8  # Set a smaller font size
        custom_style.leading = 10
        return custom_style

    def prepare_table_data(self, report_column_info, dataframe, group_colors):
        custom_style = self.get_custom_style()
        header_row = []
        header_styles = []
        self.group_colors = self.config["reports"][0]["topics"][0]["table_style"]["group_colors"]
        
        for col_idx, column_info in enumerate(report_column_info):
            column_group = column_info.get("group", "group1")
            header_bg_color = self.group_colors.get(column_group, "#FFFFFF")
            header_cell = Paragraph(f"<b>{column_info['header']}</b>", custom_style)
            header_row.append(header_cell)
            header_styles.append(("BACKGROUND", (col_idx, 0), (col_idx, 0), colors.HexColor(header_bg_color)))

        table_data = [header_row]

        for _, row in dataframe.iterrows():
            data_row = [Paragraph(str(row[col_info["column"]]), custom_style) for col_info in report_column_info]
            table_data.append(data_row)

        return table_data, header_styles

    def create_table(self, data, style_config=None, col_widths=None):
        """Create a table with the provided data and styling."""
        if not data or len(data) == 0:
            return None
        
        # Ensure we have at least one row with data
        if len(data) == 1:
            # Only header row, add an empty data row
            data.append([""] * len(data[0]))
        
        if style_config is None:
            style_config = {}
        
        # Create table style
        table_style = self.create_table_style(style_config)
        
        # Calculate available width for the table (accounting for page margins)
        available_width = self.page_width - (self.left_margin + self.right_margin)
        
        # If no column widths are provided, calculate them based on content
        if col_widths is None:
            # Get number of columns
            num_cols = len(data[0]) if data else 0
            
            if num_cols > 0:
                # Start with equal column widths
                col_widths = [available_width / num_cols] * num_cols
                
                # Analyze content to adjust column widths
                max_widths = [0] * num_cols
                for row in data:
                    for i, cell in enumerate(row):
                        if i < num_cols and isinstance(cell, str):
                            # Estimate width based on character count (approximate)
                            cell_width = min(len(cell) * 0.1 * cm, available_width * 0.4)
                            max_widths[i] = max(max_widths[i], cell_width)
                
                # Normalize widths to fit available space
                total_content_width = sum(max_widths)
                if total_content_width > 0:
                    # Scale widths proportionally if they exceed available width
                    if total_content_width > available_width:
                        scale_factor = available_width / total_content_width
                        col_widths = [width * scale_factor for width in max_widths]
                    else:
                        col_widths = max_widths
        
        # Process data to ensure text wrapping
        processed_data = []
        for row in data:
            processed_row = []
            for i, cell in enumerate(row):
                if i < len(col_widths):  # Ensure we don't exceed column widths
                    if isinstance(cell, str):
                        # Create a Paragraph with proper text wrapping
                        cell_width = col_widths[i]
                        style = ParagraphStyle(
                            name='Normal',
                            fontName='Helvetica',
                            fontSize=9,
                            leading=12,
                            alignment=1 if row == data[0] else 0  # Center for header, left for data
                        )
                        processed_row.append(Paragraph(cell, style))
                    else:
                        processed_row.append(cell)
            processed_data.append(processed_row)
        
        # Create the table with calculated column widths
        table = Table(processed_data, colWidths=col_widths)
        table.setStyle(table_style)
        
        # Ensure the table stays together if possible
        return KeepTogether(table)

    def calculate_width(self, relative_width, total_width):
        total_relative_sizes = sum(relative_width)
        return [(size / total_relative_sizes) * total_width for size in relative_width]

    def create_table_style(self, style_config):
        """Create a TableStyle based on the provided style configuration."""
        # Default style settings
        header_color = style_config.get("header_color", "#003366")
        background_color = style_config.get("background_color", "#ffffff")
        alt_background_color = style_config.get("alt_background_color", "#f5f5f5")  # Alternating row color
        text_color = style_config.get("text_color", "#000000")
        border_color = style_config.get("border_color", "#cccccc")
        
        # Convert hex colors to ReportLab colors
        header_color = colors.HexColor(header_color)
        background_color = colors.HexColor(background_color)
        alt_background_color = colors.HexColor(alt_background_color)
        text_color = colors.HexColor(text_color)
        border_color = colors.HexColor(border_color)
        
        # Create table style
        table_style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), background_color),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]
        
        return TableStyle(table_style)

    def get_scenario_filters(self, scenario_name):
        return self.scenarios[self.scenarios['name'] == scenario_name]

    def on_every_page(self, canvas, doc):
        """ Add header and footer to each page with page numbers. """
        try:
            canvas.saveState()
            
            # Use default font if not specified in config
            header_font = self.common.get("font", "Helvetica")
            header_font_size = self.common.get("header_font_size", 10)
            footer_font = self.common.get("footer_font", "Helvetica")
            footer_font_size = self.common.get("footer_font_size", 6)
            
            # Add header
            canvas.setFont(header_font, header_font_size)
            header_text = f"Page {doc.page}"
            canvas.drawString(doc.leftMargin, doc.topMargin - 30, header_text)
            
            # Add footer with page number
            canvas.setFont(footer_font, footer_font_size)
            footer_text = self.common.get("footer", "Generated Report")
            text_width = canvas.stringWidth(footer_text, footer_font, footer_font_size)
            canvas.drawString(doc.leftMargin, 15, f"Page {doc.page}")
            canvas.drawRightString(doc.width + doc.leftMargin, 15, footer_text)
            
            # Restore styles
            canvas.restoreState()
            
        except Exception as e:
            logger.error(f"Error in on_every_page: {str(e)}")
            # Continue with default styling if there's an error
            canvas.saveState()
            canvas.setFont("Helvetica", 10)
            canvas.drawString(doc.leftMargin, doc.topMargin - 30, f"Page {doc.page}")
            canvas.restoreState()

    def on_page(self, canvas, doc):
        """Add header, page number and footer to each page."""
        # Save canvas state
        canvas.saveState()
        
        # Get current page number
        page_num = getattr(doc, 'current_page', getattr(doc, 'page', 1))
        
        # Add header (except on first page which has the title)
        if page_num > 1:
            # Set font for header
            canvas.setFont('Helvetica-Bold', 10)
            
            # Draw header text at top center
            header_text = self.title
            canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 12, header_text)
            
            # Draw header line
            canvas.setStrokeColorRGB(0.8, 0.8, 0.8)  # Light gray
            canvas.line(doc.leftMargin, doc.height + doc.topMargin - 20, 
                       doc.width + doc.leftMargin, doc.height + doc.topMargin - 20)
        
        # Set font for footer
        canvas.setFont('Helvetica', 8)
        
        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Draw footer line
        canvas.setStrokeColorRGB(0.8, 0.8, 0.8)  # Light gray
        canvas.line(doc.leftMargin, 15, doc.width + doc.leftMargin, 15)
        
        # Draw page number at bottom left
        page_text = f"Page {page_num}"
        canvas.drawString(doc.leftMargin, 7, page_text)
        
        # Draw report date at bottom center
        date_text = f"Generated: {current_date}"
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, 7, date_text)
        
        # Draw footer text at bottom right
        footer_text = "Risk Oversight Report"
        canvas.drawRightString(doc.width + doc.leftMargin - 10, 7, footer_text)
        
        # Restore canvas state
        canvas.restoreState()

    def apply_filter(self, df, column, condition):
        """ Apply filters based on the condition. """
        if isinstance(condition, list):
            # Handle list of values for inclusion
            return df[df[column].isin(condition)]
        elif isinstance(condition, str):
            # Check for numeric comparison
            match = re.match(r'([<>]=?)\s*(\d+(\.\d+)?)', condition)
            if match:
                operator, value = match.groups()
                value = float(value)  # Convert value to float for comparison
                if operator == '>':
                    return df[df[column] > value]
                elif operator == '<':
                    return df[df[column] < value]
                elif operator == '>=':
                    return df[df[column] >= value]
                elif operator == '<=':
                    return df[df[column] <= value]
                elif operator == '==':
                    return df[df[column] == value]
            else:
                # Direct equality for string and non-list values
                return df[df[column] == condition]

    def fetch_filter_criteria_from_db(self, report_name, section_name):
        query = """
        SELECT COLUMN_NAME, OPERATOR, CONDITION, IS_LIST
        FROM mera_db.BOOK_CONF_FILTER_CRITERIA
        WHERE REPORT_NAME = '{report_name}' AND TABLE_NAME = '{section_name}'
        """
        result = self.db_cursor.get_df(query.format(report_name=report_name, section_name=section_name))
        return result

    def after_flowable(self, flowable):
        """ Method to register TOC entries and track page numbers. """
        if hasattr(flowable, 'getPlainText'):
            text = flowable.getPlainText()
            style_name = flowable.style.name
            
            # Check if this is a heading that should be in the TOC
            if style_name == "Heading1":
                # Register this as a level 0 (main) bookmark
                self.register_bookmark(text, level=0)
            elif style_name == "Heading2":
                # Register this as a level 1 (sub) bookmark
                self.register_bookmark(text, level=1)
                
        # Update current page number
        if hasattr(self, '_doctemplate') and hasattr(self._doctemplate, 'page'):
            self.current_page_number = self._doctemplate.page

    def build_table_of_contents(self):
        """
        Build a professional table of contents with clickable entries.
        This method is now used to create a TOC for the final PDF after all pages have been processed.
        """
        elements = []
        
        # Add TOC title
        toc_title = Paragraph("Table of Contents", self.styles["TOCTitle"])
        elements.append(toc_title)
        elements.append(Spacer(1, 20))
        
        # Get sections from the configuration
        sections = self.reports.get("sections", [])
        
        # Add TOC entries
        for section in sections:
            title = section.get("title", section.get("section_name", ""))
            
            # Create bookmark ID
            bookmark_id = title.replace(" ", "_").replace(":", "").replace(",", "").replace(".", "").lower()
            
            # Get page number from the dictionary
            page_num = self.toc_page_numbers.get(title, 1)
            
            # Format the title with dots leading to the page number
            dots = "." * (50 - len(title) - len(str(page_num)))
            if len(dots) < 5:  # Ensure minimum dots
                dots = "." * 5
            
            # Create a clickable TOC entry with an internal link
            toc_entry = Paragraph(
                f'<a href="#{bookmark_id}" color="blue">{title}</a> {dots} {page_num}',
                self.styles["TOCHeading1"]
            )
            elements.append(toc_entry)
            elements.append(Spacer(1, 4))
        
        elements.append(PageBreak())
        return elements

    def fetch_mapping_data(self):
        """ Fetch the mapping data from the database """
        mapping_query = "SELECT FULL_NAME, SHORT_NAME, TYPE FROM mera_db.BOOK.ENTITY_MAPPING"
        mapping_df = self.db_cursor.get_df(mapping_query)

        # Convert the mapping data into a dictionary organized by type
        mapping_dict = {}
        for _, row in mapping_df.iterrows():
            mapping_type = row["TYPE"]
            if mapping_type not in mapping_dict:
                mapping_dict[mapping_type] = {}
            mapping_dict[mapping_type][row["FULL_NAME"]] = row["SHORT_NAME"]

        return mapping_dict

    def apply_mapping(self, value, mapping_type):
        """ Ensure value is a scalar """
        if isinstance(value, pd.Series):
            value = value.iloc[0]

        # Apply the mapping based on the type
        if mapping_type == "FUND_NAME":
            # Check for multi-word mappings first
            for long_name, short_name in self.mapping_dict[mapping_type].items():
                if long_name in value:
                    value = value.replace(long_name, short_name)

            # Split the fund name into words and replace each word with its shorter version if a mapping exists
            words = value.split()
            mapped_words = [self.mapping_dict[mapping_type].get(word, word) for word in words]
            return " ".join(mapped_words)
        else:
            # Direct replacement for other types
            for type_dict in self.mapping_dict.values():
                if value in type_dict:
                    return type_dict[value]

    def generate_pdf_report(self, data, output_path):
        """Generate a PDF report with the provided data."""
        # First pass - collect page numbers for TOC
        buffer = BytesIO()
        first_pass_doc = FirstPassDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=self.left_margin,
            rightMargin=self.right_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin,
            title=self.title,
            author=self.author,
            subject=self.subject,
            creator=self.creator,
            producer=self.producer,
            on_page=self.on_page
        )
        
        # Build document first time to collect page numbers
        self.build_document(data, first_pass_doc)
        
        # Second pass - generate final document with TOC
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            leftMargin=self.left_margin,
            rightMargin=self.right_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin,
            title=self.title,
            author=self.author,
            subject=self.subject,
            creator=self.creator,
            producer=self.producer
        )
        
        # Copy section page map from first pass
        doc.section_page_map = first_pass_doc.section_page_map
        
        # Set on_page callback
        doc.on_page = self.on_page
        
        # Build final document with TOC
        self.build_document(data, doc)
        
        return output_path

    def get_canvas_maker(self):
        """Return a canvas maker function for the document."""
        def canvas_maker(filename, pagesize=None, **kwargs):
            from reportlab.pdfgen.canvas import Canvas
            canvas = Canvas(filename, pagesize=pagesize, **kwargs)
            return canvas
        return canvas_maker

    def register_bookmark(self, title, level=0):
        """
        Register a bookmark for the table of contents.
        
        Args:
            title (str): The title of the section to bookmark
            level (int): The level of the bookmark (0 for main sections, 1 for subsections)
        """
        # Create a bookmark ID by replacing spaces with underscores and removing special characters
        bookmark_id = title.replace(" ", "_").replace(":", "").replace(",", "").replace(".", "").lower()
        
        # Store the title, current page number, level, and bookmark ID
        self.bookmarks.append((title, self.current_page_number, level, bookmark_id))
        
        # Also store in the dictionary for easy lookup
        self.toc_page_numbers[title] = self.current_page_number

    def append_footnote_data(self, elements, shading_text, title):
        elements.append(Paragraph(f"<b>{title}:</b>", self.styles["FootnoteHeading"]))
        if isinstance(shading_text, str):
            for line in shading_text.splitlines():
                elements.append(Paragraph(f"- {line.strip()}", self.styles["FootnoteText"]))
        elif isinstance(shading_text, dict):
            for key, value in shading_text.items():
                elements.append(Paragraph(f"- {key}: {value}", self.styles["FootnoteText"]))
        else:
            print(f"Unexpected data type: {type(shading_text)}")

    def build_document(self, data, doc_template):
        """Build the document with all sections."""
        story = []
        
        # Add front page
        front_page = self.create_front_page()
        if front_page:
            story.append(front_page)
            story.append(PageBreak())
        
        # Add table of contents placeholder (will be filled in second pass)
        toc_title = Paragraph("Table of Contents", self.styles["Heading1"])
        story.append(toc_title)
        
        # Add TOC entries placeholder
        if isinstance(doc_template, FirstPassDocTemplate):
            # First pass - just collect page numbers
            story.append(Spacer(1, 2*cm))
        else:
            # Second pass - add actual TOC with page numbers
            toc_entries = []
            for section, page_num in doc_template.section_page_map.items():
                # Create TOC entry with dot leaders
                dots = "." * (50 - len(section) - len(str(page_num)))
                toc_text = f'{section} {dots} {page_num}'
                toc_style = ParagraphStyle(
                    'TOCEntry',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    leading=16,
                    leftIndent=0.5*cm,
                    firstLineIndent=-0.5*cm,
                )
                toc_entry = Paragraph(toc_text, toc_style)
                toc_entries.append(toc_entry)
                toc_entries.append(Spacer(1, 0.2*cm))
            
            story.extend(toc_entries)
        
        story.append(PageBreak())
        
        # Process each section
        for section_name, section_data in data.items():
            # Add section header
            section_header = Paragraph(section_name, self.styles["Heading1"])
            story.append(section_header)
            
            # Track section for TOC
            story.append(Spacer(1, 0.5*cm))
            
            # Process tables in the section
            for table_data in section_data:
                if "title" in table_data:
                    # Add table title
                    table_title = Paragraph(table_data["title"], self.styles["Heading2"])
                    story.append(table_title)
                    story.append(Spacer(1, 0.3*cm))
                
                if "description" in table_data:
                    # Add table description
                    table_desc = Paragraph(table_data["description"], self.styles["Normal"])
                    story.append(table_desc)
                    story.append(Spacer(1, 0.3*cm))
                
                if "data" in table_data:
                    # Create and add table
                    table = self.create_table(
                        table_data["data"],
                        style_config=table_data.get("style", {}),
                        col_widths=table_data.get("col_widths", None)
                    )
                    if table:
                        story.append(table)
                        story.append(Spacer(1, 0.5*cm))
            
            # Add page break after each section
            story.append(PageBreak())
        
        # Create a function to apply the on_page callback
        def apply_on_page(canvas, doc):
            self.on_page(canvas, doc)
        
        # Build the document with the on_page callback
        doc_template.build(story, onFirstPage=apply_on_page, onLaterPages=apply_on_page)
        
        return doc_template

    def process_data(self, df, report_config):
        """Process DataFrame data into the format needed for document building."""
        structured_data = {}
        
        # Get sections from report configuration
        sections = report_config.get("sections", [])
        
        for section in sections:
            section_name = section.get("section_name", "")
            title = section.get("title", section_name)
            description = section.get("description", "")
            
            # Filter data for this section
            section_data = df[df["section"] == section_name]
            
            # Initialize section in structured data if not exists
            if title not in structured_data:
                structured_data[title] = []
            
            # Prepare columns for the table
            columns = section.get("columns", [])
            if not columns:
                logger.warning(f"No columns defined for section: {section_name}")
                continue
            
            # Extract column names and widths
            column_names = [col.get("name") for col in columns]
            column_display_names = [col.get("display_name", col.get("name")) for col in columns]
            relative_widths = [col.get("width", 1) for col in columns]
            
            # Calculate column widths in cm
            available_width = self.page_width - (self.left_margin + self.right_margin) - 1*cm  # 1cm buffer
            col_widths = [width * available_width / sum(relative_widths) for width in relative_widths]
            
            # Prepare table data
            table_data = [column_display_names]  # Header row
            
            # Skip if no data for this section but still add the section with empty table
            if section_data.empty:
                logger.warning(f"No data found for section: {section_name}")
                # Add empty table with just headers
                table_info = {
                    "title": title,
                    "description": description,
                    "data": table_data,
                    "style": section.get("table_style", {}),
                    "col_widths": col_widths
                }
                structured_data[title].append(table_info)
                continue
            
            # Add data rows
            for _, row in section_data.iterrows():
                data_row = []
                for col_name in column_names:
                    # Get cell value, handling missing columns
                    if col_name in row:
                        cell_value = row[col_name]
                        # Format the cell value if needed
                        if pd.isna(cell_value):
                            cell_value = ""
                        elif isinstance(cell_value, float):
                            cell_value = f"{cell_value:.2f}"
                        elif isinstance(cell_value, (int, np.integer)):
                            cell_value = str(cell_value)
                        elif not isinstance(cell_value, str):
                            cell_value = str(cell_value)
                    else:
                        cell_value = ""
                    data_row.append(cell_value)
                table_data.append(data_row)
            
            # Get table style from section config
            table_style_config = section.get("table_style", {})
            
            # Add table to section
            table_info = {
                "title": title,
                "description": description,
                "data": table_data,
                "style": table_style_config,
                "col_widths": col_widths
            }
            
            structured_data[title].append(table_info)
        
        return structured_data

    def _format_date(self, value, format="%Y-%m-%d"):
        """Format a date value for templates."""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.strftime(format)
        return str(value)
    
    def _format_number(self, value, precision=2):
        """Format a number value for templates."""
        try:
            return f"{float(value):.{precision}f}"
        except (ValueError, TypeError):
            return str(value)

    def create_front_page(self):
        """Create the front page of the report."""
        try:
            # Try to use wkhtmltopdf for front page if available
            if hasattr(self, 'wkhtmltopdf_path') and self.wkhtmltopdf_path:
                # Use HTML template for front page
                template = self.jinja_env.get_template("front_page.html")
                html_content = template.render(
                    title=self.title,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    company=self.reports.get("company", "Risk Management")
                )
                
                # Create temporary HTML file
                with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html:
                    temp_html.write(html_content.encode('utf-8'))
                    temp_html_path = temp_html.name
                
                # Convert HTML to PDF using wkhtmltopdf
                temp_pdf_path = temp_html_path.replace('.html', '.pdf')
                subprocess.run([self.wkhtmltopdf_path, temp_html_path, temp_pdf_path], check=True)
                
                # Read the PDF and return as Image
                img = Image(temp_pdf_path, width=self.page_width, height=self.page_height)
                
                # Clean up temporary files
                os.remove(temp_html_path)
                os.remove(temp_pdf_path)
                
                return img
            
        except Exception as e:
            logger.warning(f"Error creating front page with wkhtmltopdf: {str(e)}")
            logger.warning("Falling back to ReportLab for front page generation")
        
        # Fallback to ReportLab for front page
        elements = []
        
        # Add logo if available
        logo_path = self.reports.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.5*inch))
        
        # Add title
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Title'],
            fontSize=24,
            leading=30,
            alignment=TA_CENTER
        )
        title = Paragraph(self.title, title_style)
        elements.append(title)
        elements.append(Spacer(1, 1*inch))
        
        # Add date
        date_style = ParagraphStyle(
            'Date',
            parent=self.styles['Normal'],
            fontSize=14,
            leading=20,
            alignment=TA_CENTER
        )
        date_text = f"Report Date: {datetime.now().strftime('%Y-%m-%d')}"
        date = Paragraph(date_text, date_style)
        elements.append(date)
        elements.append(Spacer(1, 0.5*inch))
        
        # Add company name
        company_style = ParagraphStyle(
            'Company',
            parent=self.styles['Normal'],
            fontSize=16,
            leading=20,
            alignment=TA_CENTER
        )
        company_name = self.reports.get("company", "Risk Management")
        company = Paragraph(company_name, company_style)
        elements.append(company)
        
        return KeepTogether(elements)

class FlagManager:
    def __init__(self, flag_rules):
        """Initialize FlagManager with validation of flag rules."""
        try:
            if not isinstance(flag_rules, dict):
                raise ValueError("flag_rules must be a dictionary")
            
            # Store flag rules
            self.flag_rules = flag_rules
            
            # For backward compatibility with the original format
            for category, rules in flag_rules.items():
                if isinstance(rules, list):
                    for rule in rules:
                        # Check if rule has required fields
                        if 'conditions' not in rule:
                            rule['conditions'] = []
                            # Create a condition from field, operator, value if available
                            if all(k in rule for k in ['field', 'operator', 'value']):
                                rule['conditions'].append({
                                    'field': rule['field'],
                                    'operator': rule['operator'],
                                    'value': rule['value']
                                })
                        
                        # Set default values for missing fields
                        if 'name' not in rule:
                            rule['name'] = f"Rule for {category}"
                        if 'flag_color' not in rule and 'color' not in rule:
                            rule['flag_color'] = "#ffcccc"
                        if 'text_color' not in rule:
                            rule['text_color'] = "#000000"
            
            logger.info(f"FlagManager initialized with {len(flag_rules)} rule categories")
            
        except Exception as e:
            logger.error(f"Error initializing FlagManager: {str(e)}")
            raise

    def evaluate_conditions(self, row, conditions):
        """Evaluate conditions with proper error handling and validation."""
        try:
            if not conditions:
                return False
                
            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator")
                value = condition.get("value")
                
                if not all([field, operator]):
                    logger.warning(f"Missing required condition fields: {condition}")
                    continue
                
                # Skip if field is not in the row
                if field not in row:
                    logger.warning(f"Field '{field}' not found in row")
                    continue
                
                # Get field value from row
                field_value = row[field]
                
                # Skip evaluation if field value is NaN or None
                if pd.isna(field_value):
                    continue
                
                # Evaluate the condition
                result = self._evaluate_operator(field_value, operator, value)
                
                # If any condition is false, return false (AND logic)
                if not result:
                    return False
            
            # All conditions passed
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {str(e)}")
            return False

    def _evaluate_expression(self, expression, row):
        """Safely evaluate a mathematical expression using row values."""
        try:
            # Create a safe dict with only the row values
            safe_dict = dict(row)
            # Add some safe mathematical functions
            safe_dict.update({
                'abs': abs,
                'round': round,
                'max': max,
                'min': min
            })
            return eval(expression, {"__builtins__": {}}, safe_dict)
        except Exception as e:
            logger.error(f"Error evaluating expression {expression}: {str(e)}")
            raise

    def _evaluate_operator(self, field_value, operator, value):
        """Evaluate a comparison operator."""
        try:
            # Convert value to appropriate type if needed
            if isinstance(field_value, (int, float)) and isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    pass
            
            # Handle different operators
            if operator == ">":
                return field_value > value
            elif operator == "<":
                return field_value < value
            elif operator == "==":
                return field_value == value
            elif operator == "!=":
                return field_value != value
            elif operator == ">=":
                return field_value >= value
            elif operator == "<=":
                return field_value <= value
            elif operator.lower() == "contains":
                return str(value).lower() in str(field_value).lower()
            elif operator.lower() == "startswith":
                return str(field_value).lower().startswith(str(value).lower())
            elif operator.lower() == "endswith":
                return str(field_value).lower().endswith(str(value).lower())
            else:
                logger.warning(f"Unsupported operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error comparing values ({field_value} {operator} {value}): {str(e)}")
            return False

    def save_flagged_data(self, flagged_data, table_name):
        """Save flagged data to database with proper error handling and validation."""
        if not self.db_cursor:
            logger.warning("No database cursor available. Skipping save_flagged_data.")
            return
            
        try:
            # Validate input
            if not isinstance(flagged_data, list):
                raise ValueError("flagged_data must be a list")
            
            if not table_name or not isinstance(table_name, str):
                raise ValueError("Invalid table_name")
            
            # Validate each flagged item
            for item in flagged_data:
                required_fields = ['index', 'column', 'severity', 'color', 'text_color']
                missing_fields = [field for field in required_fields if field not in item]
                if missing_fields:
                    raise ValueError(f"Missing required fields {missing_fields} in flagged item")
            
            # Prepare SQL query with proper escaping
            insert_query = f"""
                INSERT INTO {table_name} 
                (index, column_name, severity, color, text_color) 
                VALUES (%s, %s, %s, %s, %s)
            """
            
            # Prepare values for batch insert
            values = [
                (
                    item['index'],
                    item['column'],
                    item['severity'],
                    item['color'],
                    item['text_color']
                )
                for item in flagged_data
            ]
            
            # Execute batch insert
            self.db_cursor.executemany(insert_query, values)
            self.db_cursor.commit()
            
            logger.info(f"Successfully saved {len(values)} flagged items to {table_name}")
            
        except Exception as e:
            logger.error(f"Error saving flagged data: {str(e)}")
            if hasattr(self.db_cursor, 'rollback'):
                self.db_cursor.rollback()
            raise

class FirstPassDocTemplate(SimpleDocTemplate):
    """Custom document template for first pass to collect page numbers."""
    def __init__(self, *args, **kwargs):
        self.on_page = kwargs.pop('on_page', None)
        super().__init__(*args, **kwargs)
        self.section_page_map = {}
        self.current_section = None
        self.current_page = 1
    
    def handle_pageBegin(self):
        """Override to track page numbers."""
        super().handle_pageBegin()
        
        # Increment page counter
        self.current_page += 1
    
    def afterFlowable(self, flowable):
        """Track sections for TOC."""
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style == 'Heading1':
                # Extract section name from text (remove HTML tags)
                text = flowable.getPlainText()
                # Store current section and page number
                self.current_section = text
                self.section_page_map[text] = self.current_page

if __name__ == "__main__":
    # 1) Load configuration from YAML
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Ensure flag_rules key is present in the configuration
    if "flag_rules" not in config:
        config["flag_rules"] = {}

    # 2) Load data from CSV
    #    Replace 'sample_data.csv' with your actual CSV file path
    df = pd.read_csv("sample_data.csv")

    # 3) Create the engine
    #    Scenarios and db_cursor can be None or replaced with real objects if needed
    engine = ReportEngine(
        config=config,
        scenarios={},
        db_cursor=None,
        env="qa"
    )

    # 4) Generate the PDF
    #    If your YAML config has "common" -> "effective_date", we can use that
    #    Otherwise, use today's date or a custom date
    effective_date = config["common"].get("effective_date", datetime.now().strftime("%Y-%m-%d"))

    # This method uses a simple approach: front page + placeholder pages
    # engine.run_report()

    # Or use the more advanced method that expects a DataFrame
    engine.generate_pdf_report(df, effective_date)