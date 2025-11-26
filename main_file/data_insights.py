#testing the data values

import pandas as pd
from Data.datasetsql import load_data, load_unique_most_recent_data

# Correct: Call the functions directly
total_cv = load_data()
unique_users = load_unique_most_recent_data()

print(total_cv.shape)
print(unique_users.shape)
print("================================================================================================================")

categories = total_cv['application_status'].unique()
print("All unique categories:")
print(categories)

inactive_total = total_cv['application_status'].isin(['disabled', 'draft']).sum()
print(f"Inactive Total (disabled + Draft): {inactive_total}")
print(f"Original - Active: {(total_cv['application_status'] == 'active').sum()}")
"""Inactive Total (disabled + Draft): 8965
Original - Active: 11035"""
print("================================================================================================================")

inactive_total = unique_users['application_status'].isin(['disabled', 'draft']).sum()
print(f"Inactive unique users (disabled + Draft): {inactive_total}")
print(f"unique users - Active: {(unique_users['application_status'] == 'active').sum()}")
"""Inactive Total (disabled + Draft): 6768
Original - Active: 7474"""
print("================================================================================================================")

orig_counts = total_cv['applicant_location'].value_counts()
for location, count in orig_counts.items():
    print(f"{location} : {count}")
    print("================================================================================================================")

"""US : 3024
IN : 2284
GB : 1947
ZA : 1895
KE : 1742
BR : 1285
NG : 854
ES : 598
BH : 427
AT : 412
PK : 410
EC : 355
IT : 296
AR : 294
CA : 289
CL : 259
BE : 257
MA : 244
GR : 238
ID : 218
AE : 209
PH : 189
QA : 185
MX : 168
PA : 162
DE : 146
CO : 134
PE : 122
VE : 97
SA : 83
UY : 82
EG : 76
PT : 76
FR : 76
DO : 69
SG : 69
CH : 66
MY : 66
DZ : 55
CR : 53
NL : 52
KW : 49
SE : 30
PY : 29
LK : 27
GH : 27
PL : 27
TN : 26
TR : 20
GT : 20
BD : 16
PR : 14
NZ : 14
VN : 13
IE : 13
UG : 13
SV : 12
TH : 10
BO : 8
SN : 8
DK : 8
TZ : 7
AU : 7
FI : 7
OM : 7
LU : 5
MG : 4
NO : 4
UA : 3
CZ : 3
HK : 2
RU : 2
JP : 1
KR : 1"""

orig_counts = unique_users['applicant_location'].value_counts()
for location, count in orig_counts.items():
    print(f"{location} : {count}")
    print("================================================================================================================")

"""US : 2465
IN : 1610
GB : 1290
ZA : 1280
BR : 1069
KE : 891
NG : 501
ES : 463
PK : 309
EC : 280
AR : 244
CA : 226
BH : 224
AT : 224
IT : 221
CL : 215
GR : 182
AE : 165
MA : 160
BE : 158
ID : 153
PH : 146
QA : 143
MX : 142
PA : 120
CO : 113
DE : 110
PE : 98
VE : 75
SA : 66
PT : 63
UY : 61
MY : 59
DO : 57
FR : 56
CH : 53
SG : 53
EG : 50
KW : 40
CR : 40
NL : 36
DZ : 33
PY : 26
SE : 23
TN : 23
GH : 21
PL : 18
LK : 18
GT : 16
BD : 16
TR : 13
UG : 11
PR : 11
IE : 9
NZ : 9
VN : 9
BO : 8
TH : 8
AU : 7
SV : 7
FI : 7
SN : 7
DK : 6
OM : 6
TZ : 4
NO : 4
MG : 3
CZ : 2
JP : 1
KR : 1
HK : 1
RU : 1
UA : 1
LU : 1"""

# Cross tabulation - very clean output
location_status = pd.crosstab(
    total_cv['applicant_location'],
    total_cv['application_status']
)

# Add total column and sort by it
location_status['Total'] = location_status.sum(axis=1)
location_status_sorted = location_status.sort_values('Total', ascending=False)

print("Active/Inactive CV's for each Location (Sorted by Total Users):")
print(location_status_sorted)
print("================================================================================================================")

"""application_status  active  disabled  draft  Total
applicant_location                                
US                    1879         8   1137   3024
IN                    1387         8    889   2284
GB                    1156         9    782   1947
ZA                    1158         7    730   1895
KE                     983        12    747   1742
...                    ...       ...    ...    ...
CZ                       1         0      2      3
HK                       2         0      0      2
RU                       0         0      2      2
KR                       0         0      1      1
JP                       0         0      1      1"""

location_status = pd.crosstab(
    unique_users['applicant_location'],
    unique_users['application_status']
)

# Add total column and sort by it
location_status['Total'] = location_status.sum(axis=1)
location_status_sorted = location_status.sort_values('Total', ascending=False)

print("Active/Inactive Users for each Location (Sorted by Total Users):")
print(location_status_sorted)
print("================================================================================================================")

"""Active/Inactive Users per Location (Sorted by Total Users):
application_status  active  disabled  draft  Total
applicant_location                                
US                    1451         5   1009   2465
IN                     918         2    690   1610
GB                     747         3    540   1290
ZA                     724         0    556   1280
BR                     620         1    448   1069
...                    ...       ...    ...    ...
JP                       0         0      1      1
LU                       0         0      1      1
KR                       0         0      1      1
RU                       0         0      1      1
UA                       0         0      1      1
"""


categories = total_cv['dtype'].unique()
print("All unique categories:")
print(categories)

device_total = total_cv['dtype'].isin(['mobile']).sum()
print(f"mobile CV's: {device_total}")
print(f"desktop CV's: {(total_cv['dtype'] == 'desktop').sum()}")
print("================================================================================================================")

"""mobile CV's: 10107
desktop CV's: 9893
"""

device_total = unique_users['dtype'].isin(['mobile']).sum()
print(f"mobile Users: {device_total}")
print(f"desktop Users: {(unique_users['dtype'] == 'desktop').sum()}")
print("================================================================================================================")

"""mobile Users: 7255
desktop Users: 6987
"""

location_status = pd.crosstab(
    total_cv['dtype'],
    total_cv['applicant_location'],

)

# Add total column and sort by it
location_status['Total'] = location_status.sum(axis=1)
location_status_sorted = location_status.sort_values('Total', ascending=False)

print("desktop/mobile CV's per Location (Sorted by Total Users):")
print(location_status_sorted)
print("================================================================================================================")

"""desktop/mobile CV's per Location (Sorted by Total Users):
applicant_location   AE   AR   AT  AU  BD   BE  ...    US  UY  VE  VN    ZA  Total
dtype                                           ...                               
mobile               94  163  123   1   6   93  ...  1551  41  64   1  1051  10107
desktop             115  131  289   6  10  164  ...  1473  41  33  12   844   9893
"""

location_status = pd.crosstab(
    unique_users['dtype'],
    unique_users['applicant_location'],

)

# Add total column and sort by it
location_status['Total'] = location_status.sum(axis=1)
location_status_sorted = location_status.sort_values('Total', ascending=False)

print("desktop/mobile Users per Location (Sorted by Total Users):")
print(location_status_sorted)
print("================================================================================================================")

"""desktop/mobile CV's per Location (Sorted by Total Users):
applicant_location   AE   AR   AT  AU  BD   BE  ...    US  UY  VE  VN    ZA  Total
dtype                                           ...                               
mobile               94  163  123   1   6   93  ...  1551  41  64   1  1051  10107
desktop             115  131  289   6  10  164  ...  1473  41  33  12   844   9893
"""

location_status = pd.crosstab(
    total_cv['applicant_location'],
    total_cv['regsource'],

)

# Add total column and sort by it
location_status['Total'] = location_status.sum(axis=1)
location_status_sorted = location_status.sort_values('Total', ascending=False)

print("registerSource by applicant_location(Sorted by Total Users):")
print(location_status_sorted)
print("================================================================================================================")

"""registerSource by applicant_location(Sorted by Total Users):
regsource              JobSeeker Dashboard  ...  search  Total
applicant_location                          ...               
US                  0                   65  ...       7   3024
IN                  2                   50  ...      11   2284
GB                  2                   70  ...       6   1947
ZA                  1                   67  ...       9   1895
KE                  4                  162  ...       3   1742
...                ..                  ...  ...     ...    ...
CZ                  0                    0  ...       0      3
HK                  0                    0  ...       0      2
RU                  0                    0  ...       0      2
KR                  0                    0  ...       0      1
JP                  0                    0  ...       0      1
"""

location_status = pd.crosstab(
    unique_users['applicant_location'],
    unique_users['regsource'],

)

# Add total column and sort by it
location_status['Total'] = location_status.sum(axis=1)
location_status_sorted = location_status.sort_values('Total', ascending=False)

print("registerSource by applicant_location (Sorted by unique Users):")
print(location_status_sorted)
print("================================================================================================================")

"""registerSource by applicant_location (Sorted by unique Users):
regsource              JobSeeker Dashboard  ...  search  Total
applicant_location                          ...               
US                  0                   42  ...       3   2465
IN                  1                   25  ...       5   1610
GB                  2                   27  ...       3   1290
ZA                  0                   25  ...       2   1280
BR                  0                    0  ...       0   1069
...                ..                  ...  ...     ...    ...
JP                  0                    0  ...       0      1
LU                  0                    0  ...       0      1
KR                  0                    0  ...       0      1
RU                  0                    0  ...       0      1
UA                  0                    0  ...       0      1"""