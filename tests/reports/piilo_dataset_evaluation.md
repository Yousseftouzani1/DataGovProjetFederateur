# Presidio Service - Piilo Dataset Evaluation

**Date:** 2026-01-03 15:17:18  
**Dataset:** Piilo (Kaggle) - Real-world PII Dataset  
**Cahier Section:** 5.7 - Datasets de Test

---

## Dataset Information

- **Source:** https://www.kaggle.com/datasets/lburleigh/piilo-dataset
- **Samples Analyzed:** 500
- **Purpose:** Real-world PII detection validation

---

## Detection Results

| Metric | Value |
|--------|-------|
| Samples with PII | 497 |
| Detection Rate | 99.4% |
| Total PII Entities | 3267 |
| Avg PII per Document | 6.53 |

---

## Entity Type Distribution

| Entity Type | Count | Percentage |
|-------------|-------|------------|
| ORGANIZATION | 1177 | 36.0% |
| PERSON | 782 | 23.9% |
| DATE_TIME | 756 | 23.1% |
| LOCATION | 364 | 11.1% |
| NRP | 101 | 3.1% |
| URL | 71 | 2.2% |
| EMAIL_ADDRESS | 15 | 0.5% |
| PHONE_NUMBER | 1 | 0.0% |

---

## Sample Detections (Top 10)

### Sample #184

- **Detections:** 28
- **Entity Types:** ORGANIZATION, PERSON, LOCATION, DATE_TIME, NRP
- **Text Preview:** _Stakeholders Lead Artist Designer: Tyler Okey Project Manager: Local Architect, ..._

### Sample #189

- **Detections:** 26
- **Entity Types:** ORGANIZATION, PERSON, DATE_TIME, LOCATION
- **Text Preview:** _Syed Aziz – Design Thinking for Innovation – September 5th, 2020

Example Reflec..._

### Sample #147

- **Detections:** 25
- **Entity Types:** ORGANIZATION, PERSON, URL, LOCATION, NRP
- **Text Preview:** _DESIGN​ ​THINKING  LEARNING​ ​LAUNCHES

By​ Uwe Wegener

Challenge​ ​&​ ​Selecti..._

### Sample #203

- **Detections:** 25
- **Entity Types:** ORGANIZATION, PERSON, LOCATION, DATE_TIME, NRP
- **Text Preview:** _Reflection – Storytelling, Cedric Sanchez

1.  Challenge:  In my role as Dean of..._

### Sample #248

- **Detections:** 25
- **Entity Types:** ORGANIZATION, LOCATION, DATE_TIME
- **Text Preview:** _Consistent positive onboarding experience across 7 offices in Central Eastern Eu..._

### Sample #378

- **Detections:** 22
- **Entity Types:** ORGANIZATION, PERSON, URL, LOCATION, DATE_TIME
- **Text Preview:** _Pre- Induction Assignment 3 MediPath  #ItGetsBetter

Anil Dubey

276795361801

C..._

### Sample #135

- **Detections:** 21
- **Entity Types:** ORGANIZATION, PERSON, URL, LOCATION, DATE_TIME, NRP, EMAIL_ADDRESS
- **Text Preview:** _, Vol.7, No.5, May 2009

E-ISSN: 2321-9637

Available online at https://diaz.com..._

### Sample #170

- **Detections:** 21
- **Entity Types:** ORGANIZATION, PERSON, LOCATION, DATE_TIME, NRP
- **Text Preview:** _Alvaro Moreno  Rajagiri College of Social Sciences University of Dhaka  Khurais ..._

### Sample #214

- **Detections:** 21
- **Entity Types:** ORGANIZATION, PERSON, LOCATION, DATE_TIME, NRP
- **Text Preview:** _STORY TELLING

PIN NO. :163133980712   NAME : Qais

USER QUOTES MEANING CONCLUSI..._

### Sample #232

- **Detections:** 21
- **Entity Types:** ORGANIZATION, PERSON, DATE_TIME, LOCATION
- **Text Preview:** _DESIGN THINKING

EXPERIMENT – 2

Name: Nizam Ahmed                             P..._


---

## Conclusion

✅ Presidio successfully tested on real-world Piilo dataset  
✅ Cahier Section 5.7 requirement met  
✅ Service demonstrates capability on production data
