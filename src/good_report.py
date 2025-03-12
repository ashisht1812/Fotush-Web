    def build_table_of_contents(self):
        """Build a professional table of contents with modern styling and clickable bookmarks."""
        elements = []
        
        # Add TOC title
        toc_title = Paragraph("Table of Contents", self.styles["TOCTitle"])
        elements.append(toc_title)
        
        # Add horizontal line
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.black,
            spaceBefore=5,
            spaceAfter=20,
            lineCap=1
        ))
        
        # Get sections from configuration
        sections = self.reports.get("sections", [])
        section_counter = 1
        
        for section in sections:
            title = section.get("title", section.get("section_name", ""))
            subsections = section.get("subsections", [])
            page_num = self.bookmarks.get(title, 1)
            
            # Create bookmark key
            bookmark_key = f"section_{section_counter}"
            
            # Format main section with link
            dots = "." * (70 - len(f"{section_counter}. {title}") - len(str(page_num)))
            toc_text = f'<link href="#{bookmark_key}"><b>{section_counter}. {title}</b>{dots}{page_num}</link>'
            elements.append(Paragraph(toc_text, self.styles["TOCHeading1"]))
            
            # Store bookmark for this section
            self.bookmarks[bookmark_key] = page_num
            
            # Format subsections
            if subsections:
                for sub_idx, subsection in enumerate(subsections, 1):
                    sub_title = subsection.get("title", "")
                    sub_page = self.bookmarks.get(f"{title}:{sub_title}", page_num)
                    
                    # Create bookmark key for subsection
                    sub_bookmark_key = f"section_{section_counter}_{sub_idx}"
                    
                    sub_dots = "." * (65 - len(f"{section_counter}.{sub_idx} {sub_title}") - len(str(sub_page)))
                    sub_text = f'<link href="#{sub_bookmark_key}">{section_counter}.{sub_idx} {sub_title}{sub_dots}{sub_page}</link>'
                    elements.append(Paragraph(sub_text, self.styles["TOCHeading2"]))
                    
                    # Store bookmark for this subsection
                    self.bookmarks[sub_bookmark_key] = sub_page
            
            section_counter += 1
        
        elements.append(PageBreak())
        return elements

    def on_page(self, canvas, doc):
        """Add professional header and footer to each page with bookmark support."""
        canvas.saveState()
        
        # Get current page number
        page_num = doc.page
        
        # Add header (except on first page)
        if page_num > 1:
            # Header text
            canvas.setFont('Helvetica-Bold', 10)
            header_text = self.reports.get("title", "Report")
            canvas.drawCentredString(self.page_width/2, self.page_height - 20, header_text)
            
            # Header line
            canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
            canvas.line(self.left_margin, self.page_height - 30,
                       self.page_width - self.right_margin, self.page_height - 30)
        
        # Footer
        canvas.setFont('Helvetica', 8)
        
        # Footer line
        canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
        canvas.line(self.left_margin, 30,
                   self.page_width - self.right_margin, 30)
        
        # Page number
        page_text = f"Page {page_num}"
        canvas.drawString(self.left_margin, 15, page_text)
        
        # Date
        date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
        canvas.drawCentredString(self.page_width/2, 15, date_text)
        
        # Report name
        footer_text = self.reports.get("name", "Report")
        canvas.drawRightString(self.page_width - self.right_margin, 15, footer_text)
        
        # Add bookmarks for the current page
        for bookmark_key, bookmark_page in self.bookmarks.items():
            if bookmark_page == page_num:
                canvas.bookmarkPage(bookmark_key)
        
        canvas.restoreState()

    def generate_report_pages(self):
        """Generate report pages using ReportLab with bookmark support."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        
        # Add sections with bookmarks
        section_counter = 1
        for section in self.reports.get("sections", []):
            title = section.get("title", section.get("section_name", ""))
            bookmark_key = f"section_{section_counter}"
            
            # Add section title with bookmark
            section_title = Paragraph(title, self.styles["Heading1"])
            section_title.bookmarkName = bookmark_key
            elements.append(section_title)
            
            # Add subsections with bookmarks if they exist
            if section.get("subsections"):
                for sub_idx, subsection in enumerate(section["subsections"], 1):
                    sub_title = subsection.get("title", "")
                    sub_bookmark_key = f"section_{section_counter}_{sub_idx}"
                    
                    # Add subsection title with bookmark
                    sub_title_elem = Paragraph(sub_title, self.styles["Heading2"])
                    sub_title_elem.bookmarkName = sub_bookmark_key
                    elements.append(sub_title_elem)
            
            section_counter += 1
        
        elements.append(PageBreak())
        doc.build(elements, onFirstPage=self.on_page, onLaterPages=self.on_page)
        return buffer.getvalue()