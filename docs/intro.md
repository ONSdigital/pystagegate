# Introduction to Pystagegate

Pystagegate is a Python package implementing Stage Gate automated quality assurance methods for demographic data. 
Stage Gate methods were designed by the Office of National Statistics Population and Migration R&D division.

Pystagegate ingests CSV files and uses the Pandas DataFrame library for data processing and Pandera for data validation. There are three complete data pipelines contained in the package:
 1. **Provisional-Final**
 2. **Sex-Ratio**
 3. **National Profile**


The **Provisional-Final** pipeline collates final migration data and provisional migration, producing sums of squared differences between final migration estimates and provisional migration estimates. 


The **Sex-Ratio** pipeline looks at Male and Female migration estimates across two years of final migration data and computes Male-Female sex ratios at the local authority and national level.

The **National Profile** pipeline again looks at migration estimates across two years of final migration data and produces sums of squared differences at the local authority and national level.