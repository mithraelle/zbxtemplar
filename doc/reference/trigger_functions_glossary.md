# Trigger Functions Glossary

Use these wrapper classes to build trigger expressions. Import `functions` from a
versioned catalog such as `zbxtemplar.catalog.zabbix_7_4`, then call wrappers like
`functions.history.Last(item)` or `functions.aggregate.Min(item, "5m")`.

The `Args` column lists the Python wrapper arguments after the implicit function name.
Use normal expression-builder operators around these calls, for example
`functions.history.Last(item) > 90`.

## Aggregate functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `avg` | `functions.aggregate.Avg` | `item_or_foreach, period=None` | The average value of an item within the defined evaluation period. |
| `bucket_percentile` | `functions.aggregate.BucketPercentile` | `item_filter, time_period, percentage` | Calculates the percentile from the buckets of a histogram. |
| `count` | `functions.aggregate.Count` | `foreach_result` | The count of values in an array returned by a foreach function. |
| `histogram_quantile` | `functions.aggregate.HistogramQuantile` | `phi, bucket_rate_foreach` | Calculates the phi-quantile from the buckets of a histogram. |
| `item_count` | `functions.aggregate.ItemCount` | `item_filter` | The count of existing items in configuration that match the filter criteria. |
| `kurtosis` | `functions.aggregate.Kurtosis` | `item, period` | The "tailedness" of the probability distribution in collected values within the defined evaluation period. |
| `mad` | `functions.aggregate.Mad` | `item, period` | The median absolute deviation in collected values within the defined evaluation period. |
| `max` | `functions.aggregate.Max` | `item_or_foreach, period=None` | The highest value of an item within the defined evaluation period. |
| `min` | `functions.aggregate.Min` | `item_or_foreach, period=None` | The lowest value of an item within the defined evaluation period. |
| `skewness` | `functions.aggregate.Skewness` | `item, period` | The asymmetry of the probability distribution in collected values within the defined evaluation period. |
| `stddevpop` | `functions.aggregate.Stddevpop` | `item, period` | The population standard deviation in collected values within the defined evaluation period. |
| `stddevsamp` | `functions.aggregate.Stddevsamp` | `item, period` | The sample standard deviation in collected values within the defined evaluation period. |
| `sum` | `functions.aggregate.Sum` | `item_or_foreach, period=None` | The sum of collected values within the defined evaluation period. |
| `sumofsquares` | `functions.aggregate.Sumofsquares` | `item, period` | The sum of squares in collected values within the defined evaluation period. |
| `varpop` | `functions.aggregate.Varpop` | `item, period` | The population variance of collected values within the defined evaluation period. |
| `varsamp` | `functions.aggregate.Varsamp` | `item, period` | The sample variance of collected values within the defined evaluation period. |

## Foreach functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `avg_foreach` | `functions.aggregate.AvgForeach` | `item_filter, period` | Returns the average value for each item. |
| `bucket_rate_foreach` | `functions.aggregate.BucketRateForeach` | `item_filter, period, param_number` | Returns pairs (bucket upper bound, rate value) suitable for use in histogram_quantile(); the bucket upper bound is the item key parameter defined by the parameter number. |
| `count_foreach` | `functions.aggregate.CountForeach` | `item_filter, period` | Returns the number of values for each item. |
| `exists_foreach` | `functions.aggregate.ExistsForeach` | `item_filter` | Returns '1' for each enabled item. |
| `last_foreach` | `functions.aggregate.LastForeach` | `item_filter` | Returns the last value for each item. |
| `max_foreach` | `functions.aggregate.MaxForeach` | `item_filter, period` | Returns the maximum value for each item. |
| `min_foreach` | `functions.aggregate.MinForeach` | `item_filter, period` | Returns the minimum value for each item. |
| `sum_foreach` | `functions.aggregate.SumForeach` | `item_filter, period` | Returns the sum of values for each item. |

## Bitwise functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `bitand` | `functions.bitwise.Bitand` | `value, mask` | The value of bitwise AND of an item value and mask. |
| `bitlshift` | `functions.bitwise.Bitlshift` | `value, bits` | The bitwise shift left of an item value. |
| `bitnot` | `functions.bitwise.Bitnot` | `value` | The value of bitwise NOT of an item value. |
| `bitor` | `functions.bitwise.Bitor` | `value, mask` | The value of bitwise OR of an item value and mask. |
| `bitrshift` | `functions.bitwise.Bitrshift` | `value, bits` | The bitwise shift right of an item value. |
| `bitxor` | `functions.bitwise.Bitxor` | `value, mask` | The value of bitwise exclusive OR of an item value and mask. |

## Date and time functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/time>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `date` | `functions.time.Date` | `()` | The current date in YYYYMMDD format. |
| `dayofmonth` | `functions.time.Dayofmonth` | `()` | The day of month in range of 1 to 31. |
| `dayofweek` | `functions.time.Dayofweek` | `()` | The day of week in range of 1 to 7. |
| `now` | `functions.time.Now` | `()` | The number of seconds since the Epoch (00:00:00 UTC, January 1, 1970). |
| `time` | `functions.time.Time` | `()` | The current time in HHMMSS format. |

## History functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `change` | `functions.history.Change` | `item` | The amount of difference between the previous and latest value. |
| `changecount` | `functions.history.Changecount` | `item, period, mode=None` | The number of changes between adjacent values within the defined evaluation period. |
| `count` | `functions.history.Count` | `item, period, operator=None, pattern=None` | The number of values within the defined evaluation period. |
| `countunique` | `functions.history.Countunique` | `item, period, operator=None, pattern=None` | The number of unique values within the defined evaluation period. |
| `find` | `functions.history.Find` | `item, period, operator, pattern` | Find a value match within the defined evaluation period. |
| `first` | `functions.history.First` | `item, period` | The first (the oldest) value within the defined evaluation period. |
| `firstclock` | `functions.history.Firstclock` | `item, period` | The timestamp of the first (the oldest) value within the defined evaluation period. |
| `fuzzytime` | `functions.history.Fuzzytime` | `item, sec` | Check how much the passive agent time differs from the Zabbix server/proxy time. |
| `last` | `functions.history.Last` | `item, period=None` | The most recent value. |
| `lastclock` | `functions.history.Lastclock` | `item, period=None` | The timestamp of the Nth most recent value within the defined evaluation period. |
| `logeventid` | `functions.history.Logeventid` | `item, pattern=None` | Check if the event ID of the last log entry matches a regular expression. |
| `logseverity` | `functions.history.Logseverity` | `item` | The log severity of the last log entry. |
| `logsource` | `functions.history.Logsource` | `item, pattern=None` | Check if log source of the last log entry matches a regular expression. |
| `logtimestamp` | `functions.history.Logtimestamp` | `item, period=None` | The log message timestamp of the Nth most recent log item value. |
| `monodec` | `functions.history.Monodec` | `item, period, mode=None` | Check if there has been a monotonous decrease in values. |
| `monoinc` | `functions.history.Monoinc` | `item, period, mode=None` | Check if there has been a monotonous increase in values. |
| `nodata` | `functions.history.Nodata` | `item, sec, mode=None` | Check for no data received. |
| `percentile` | `functions.history.Percentile` | `item, period, percentage` | The P-th percentile of a period, where P (percentage) is specified by the third parameter. |
| `rate` | `functions.history.Rate` | `item, period` | The per-second average rate of the increase in a monotonically increasing counter within the defined time period. |

## Trend functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `baselinedev` | `functions.trends.Baselinedev` | `item, data_period, season_unit, num_seasons` | Returns the number of deviations (by stddevpop algorithm) between the last data period and the same data periods in preceding seasons. |
| `baselinewma` | `functions.trends.Baselinewma` | `item, data_period, season_unit, num_seasons` | Calculates the baseline by averaging data from the same timeframe in multiple equal time periods ('seasons') using the weighted moving average algorithm. |
| `trendavg` | `functions.trends.Trendavg` | `item, period` | The average of trend values within the defined time period. |
| `trendcount` | `functions.trends.Trendcount` | `item, period` | The number of successfully retrieved history values used to calculate the trend value within the defined time period. |
| `trendmax` | `functions.trends.Trendmax` | `item, period` | The maximum in trend values within the defined time period. |
| `trendmin` | `functions.trends.Trendmin` | `item, period` | The minimum in trend values within the defined time period. |
| `trendstl` | `functions.trends.Trendstl` | `item, detection_period, season, trend, deviations=None, algorithm=None` | Returns the rate of anomalies during the detection period: number of anomaly values divided by total number of values, as a decimal between 0 and 1. |
| `trendsum` | `functions.trends.Trendsum` | `item, period` | The sum of trend values within the defined time period. |

## Mathematical functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `abs` | `functions.math.Abs` | `value` | The absolute value of a value. |
| `acos` | `functions.math.Acos` | `value` | The arccosine of a value as an angle, expressed in radians. |
| `asin` | `functions.math.Asin` | `value` | The arcsine of a value as an angle, expressed in radians. |
| `atan` | `functions.math.Atan` | `value` | The arctangent of a value as an angle, expressed in radians. |
| `atan2` | `functions.math.Atan2` | `value, abscissa` | The arctangent of the ordinate (value) and abscissa coordinates specified as an angle, expressed in radians. |
| `avg` | `functions.math.Avg` | `*values` | The average value of the referenced item values. |
| `cbrt` | `functions.math.Cbrt` | `value` | The cube root of a value. |
| `ceil` | `functions.math.Ceil` | `value` | Round the value up to the nearest greater or equal integer. |
| `cos` | `functions.math.Cos` | `value` | The cosine of a value, where the value is an angle expressed in radians. |
| `cosh` | `functions.math.Cosh` | `value` | The hyperbolic cosine of a value. |
| `cot` | `functions.math.Cot` | `value` | The cotangent of a value, where the value is an angle expressed in radians. |
| `degrees` | `functions.math.Degrees` | `value` | Converts a value from radians to degrees. |
| `e` | `functions.math.E` | `()` | Euler's number (2.718281828459045). |
| `exp` | `functions.math.Exp` | `value` | Euler's number at a power of a value. |
| `expm1` | `functions.math.Expm1` | `value` | Euler's number at a power of a value minus 1. |
| `floor` | `functions.math.Floor` | `value` | Round the value down to the nearest smaller or equal integer. |
| `log` | `functions.math.Log` | `value` | The natural logarithm. |
| `log10` | `functions.math.Log10` | `value` | The decimal logarithm. |
| `max` | `functions.math.Max` | `*values` | The highest value of the referenced item values. |
| `min` | `functions.math.Min` | `*values` | The lowest value of the referenced item values. |
| `mod` | `functions.math.Mod` | `value, divisor` | The division remainder. |
| `pi` | `functions.math.Pi` | `()` | The Pi constant (3.14159265358979). |
| `power` | `functions.math.Power` | `value, power` | The power of a value. |
| `radians` | `functions.math.Radians` | `value` | Converts a value from degrees to radians. |
| `rand` | `functions.math.Rand` | `()` | Return a random integer value. |
| `round` | `functions.math.Round` | `value, precision=None` | Round the value to decimal places. |
| `signum` | `functions.math.Signum` | `value` | Returns '-1' if a value is negative, '0' if a value is zero, '1' if a value is positive. |
| `sin` | `functions.math.Sin` | `value` | The sine of a value, where the value is an angle expressed in radians. |
| `sinh` | `functions.math.Sinh` | `value` | The hyperbolical sine of a value, where the value is an angle expressed in radians. |
| `sqrt` | `functions.math.Sqrt` | `value` | The square root of a value. |
| `sum` | `functions.math.Sum` | `*values` | The sum of the referenced item values. |
| `tan` | `functions.math.Tan` | `value` | The tangent of a value. |
| `truncate` | `functions.math.Truncate` | `value, precision=None` | Truncate the value to decimal places. |

## Operator functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/operator>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `between` | `functions.operator.Between` | `value, min, max` | Check if the value belongs to the given range. |
| `in` | `functions.operator.In` | `value, *values` | Check if the value is equal to at least one of the listed values. |

## Predictive functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/prediction>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `forecast` | `functions.prediction.Forecast` | `item, period, time, fit=None, mode=None` | The future value, max, min, delta or avg of the item. |
| `timeleft` | `functions.prediction.Timeleft` | `item, period, threshold, fit=None` | The time in seconds needed for an item to reach the specified threshold. |

## String functions

Source: <https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string>

| Zabbix function | Python wrapper | Args | Meaning |
|---|---|---|---|
| `ascii` | `functions.string.Ascii` | `value` | The ASCII code of the leftmost character of the value. |
| `bitlength` | `functions.string.Bitlength` | `value` | The length of value in bits. |
| `bytelength` | `functions.string.Bytelength` | `value` | The length of value in bytes. |
| `char` | `functions.string.Char` | `value` | Return the character by interpreting the value as ASCII code. |
| `concat` | `functions.string.Concat` | `*values` | The string resulting from concatenating the referenced item values or constant values. |
| `insert` | `functions.string.Insert` | `value, start, length, replacement` | Insert specified characters or spaces into the character string beginning at the specified position in the string. |
| `jsonpath` | `functions.string.Jsonpath` | `value, path, default=None` | Return the JSONPath result. |
| `left` | `functions.string.Left` | `value, count` | Return the leftmost characters of the value. |
| `length` | `functions.string.Length` | `value` | The length of value in characters. |
| `ltrim` | `functions.string.Ltrim` | `value, characters=None` | Remove specified characters from the beginning of string. |
| `mid` | `functions.string.Mid` | `value, start, count` | Return a substring of N characters beginning at the character position specified by 'start'. |
| `repeat` | `functions.string.Repeat` | `value, count` | Repeat a string. |
| `replace` | `functions.string.Replace` | `value, pattern, replacement` | Find the pattern in the value and replace with replacement. |
| `right` | `functions.string.Right` | `value, count` | Return the rightmost characters of the value. |
| `rtrim` | `functions.string.Rtrim` | `value, characters=None` | Remove specified characters from the end of string. |
| `trim` | `functions.string.Trim` | `value, characters=None` | Remove specified characters from the beginning and end of string. |
| `xmlxpath` | `functions.string.Xmlxpath` | `value, path, default=None` | Return the XML XPath result. |
