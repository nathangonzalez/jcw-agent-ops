# JCW Welton Construction — Website Redesign Brief

**Date:** 2026-02-22  
**Status:** DRAFT — Pending owner approval  
**Domain:** jcweltonconstruction.com  

---

## 1. Executive Summary

Redesign jcweltonconstruction.com as a modern, mobile-first marketing website that establishes JCW Welton Construction as a premium residential contractor in the greater Philadelphia / Main Line area. The site should generate leads, showcase completed projects, and reinforce trust through professional presentation.

---

## 2. Business Goals

| Priority | Goal | Success Metric |
|----------|------|----------------|
| 1 | Generate inbound leads (phone/form) | ≥5 contact form submissions/month |
| 2 | Showcase project portfolio | Photo gallery with ≥20 projects |
| 3 | Establish credibility & trust | Testimonials, licensing, insurance badges |
| 4 | Mobile-first experience | 90+ Lighthouse mobile score |
| 5 | SEO for local search | Rank top-5 for "custom home builder Main Line PA" |

---

## 3. Target Audience

- **Primary:** Homeowners in Main Line / Philadelphia suburbs planning renovations, additions, or custom builds ($100K–$2M+ projects)
- **Secondary:** Architects, designers, and real estate agents looking for a reliable GC to refer
- **Tertiary:** Potential employees / subcontractors evaluating JCW as a workplace

---

## 4. Sitemap

```
jcweltonconstruction.com/
├── Home (/)
│   ├── Hero: tagline + CTA → Contact
│   ├── Featured Projects (3 rotating)
│   ├── Services overview (icons + links)
│   ├── Testimonials carousel
│   └── Footer: contact info, license #, social
│
├── About (/about)
│   ├── Company story & mission
│   ├── Meet the team (photos + bios)
│   ├── Licensing & insurance details
│   └── Awards / certifications
│
├── Services (/services)
│   ├── Custom Home Building
│   ├── Renovations & Additions
│   ├── Kitchen & Bath Remodels
│   ├── Historic Restoration
│   ├── Project Management / GC Services
│   └── Each service → detail page with gallery
│
├── Portfolio (/portfolio)
│   ├── Filterable gallery (by service type, location)
│   ├── Project detail pages with:
│   │   ├── Before/after photos
│   │   ├── Project scope & timeline
│   │   └── Client testimonial
│   └── Lightbox photo viewer
│
├── Testimonials (/testimonials)
│   ├── Client reviews with names + project type
│   ├── Google Reviews integration
│   └── Video testimonials (if available)
│
├── Contact (/contact)
│   ├── Contact form (name, email, phone, project type, budget range, message)
│   ├── Phone number (click-to-call)
│   ├── Email
│   ├── Office address + Google Maps embed
│   └── Service area map
│
├── Blog (/blog) [Phase 2]
│   ├── Construction tips & trends
│   ├── Project spotlights
│   └── SEO content for local keywords
│
└── Careers (/careers) [Phase 2]
    ├── Open positions
    ├── Company culture
    └── Application form
```

---

## 5. Design Direction

### 5.1 Visual Style
- **Clean, modern, professional** — not flashy or overly corporate
- Navy blue (#1B365D) + warm gold/amber accent (#D4A843) + white/light gray
- Large hero photography with subtle overlay text
- Consistent spacing, generous whitespace

### 5.2 Typography
- **Headings:** Serif (e.g., Playfair Display or Merriweather) for premium feel
- **Body:** Clean sans-serif (e.g., Inter or Source Sans Pro)
- Minimum 16px body, 1.5 line height for readability

### 5.3 Photography
- Professional project photography is CRITICAL
- Before/after capability
- Team photos (job site + professional headshots)
- Drone shots if available for larger projects

### 5.4 Mobile-First
- Hamburger nav on mobile, sticky header on scroll
- Touch-friendly gallery with swipe gestures
- Click-to-call phone numbers prominent
- Fast load (<3s on 4G)

---

## 6. Technical Requirements

| Requirement | Recommendation |
|-------------|----------------|
| Framework | Next.js 14+ (React SSR/SSG) or Astro for static |
| Hosting | Vercel or Cloudflare Pages (CDN-first) |
| CMS | Headless CMS (Sanity.io or Contentful) for portfolio + blog |
| Forms | FormSpree or custom API → email + Slack notification |
| Analytics | Google Analytics 4 + Search Console |
| SEO | Structured data (LocalBusiness schema), sitemap.xml, meta tags |
| SSL | Required (auto via Vercel/Cloudflare) |
| Domain | Keep jcweltonconstruction.com, add www redirect |
| Performance | Target Lighthouse 90+ on all categories |
| Accessibility | WCAG 2.1 AA compliance |

---

## 7. Content Needs (from client)

- [ ] Company bio/story (500-1000 words)
- [ ] Team bios + headshots
- [ ] Project photos (organized by project, min 5 per project)
- [ ] Client testimonials (with permission to use names)
- [ ] Service descriptions (or approve AI-drafted versions)
- [ ] License numbers, insurance details
- [ ] Preferred contact info (phone, email, address)
- [ ] Logo files (SVG + PNG, light + dark versions)
- [ ] Any existing brand guidelines

---

## 8. Competitive Reference Sites

These are examples of the visual quality and professionalism to target:
1. **Mangan Group Architects** — clean portfolio presentation
2. **K Hovnanian** — service page structure
3. **Bancroft Construction** — local PA contractor, good portfolio layout
4. **Period Architecture** — historic restoration portfolio

---

## 9. Timeline (Proposed)

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1: Design | 2 weeks | Wireframes, design mockups (Figma) |
| Phase 2: Development | 3 weeks | Coded site, CMS setup, content entry |
| Phase 3: Content | 1 week (parallel) | Photo editing, copywriting, SEO optimization |
| Phase 4: Launch | 1 week | Testing, DNS cutover, analytics setup |
| **Total** | **~6 weeks** | Live redesigned site |

---

## 10. Budget Considerations

| Approach | Est. Cost | Pros | Cons |
|----------|----------|------|------|
| AI-assisted build (in-house) | $0-500 | Fast, full control, no vendor | Needs photo content |
| Template + customization | $500-2K | Quick start | Generic feel |
| Agency redesign | $5K-15K | Professional, turnkey | Timeline, cost |

**Recommendation:** AI-assisted build using Next.js + Sanity CMS. Cline can scaffold the entire site. Primary investment is professional photography.

---

## 11. Next Steps

1. **Nathan reviews this brief** and provides feedback
2. Gather content (photos, bios, testimonials)
3. Create wireframes in Figma or direct to code
4. Build site scaffold with placeholder content
5. Populate with real content as provided
6. Test on mobile + desktop
7. DNS cutover and launch

---

*Prepared by Cline AI — Sprint Board Item: Product: JCW Website Redesign*