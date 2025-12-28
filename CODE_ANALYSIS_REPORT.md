# Code Analysis Report - Injury Prediction System

**Total Bugs Found:** 30
**Total Warnings:** 324

## Bugs Found

### HIGH Severity (9 bugs)

1. **[Security Issue]** Dangerous function __import__ used
   - Location: `qa_test_suite.py:296`

2. **[Security Issue]** Dangerous function __import__ used
   - Location: `qa_test_suite.py:325`

3. **[Security Issue]** Dangerous function __import__ used
   - Location: `qa_test_suite.py:362`

4. **[Security Issue]** Dangerous function eval( used
   - Location: `code_analysis_test.py:83`

5. **[Security Issue]** Dangerous function exec( used
   - Location: `code_analysis_test.py:83`

6. **[Security Issue]** Dangerous function __import__ used
   - Location: `code_analysis_test.py:83`

7. **[Security Issue]** Hardcoded secret found in code
   - Location: `explored_unused_solutions/strava/strava_dat.py:8`

8. **[Security Issue]** Dangerous function eval( used
   - Location: `explored_unused_solutions/Garmin/process_data.py:133`

9. **[Security Issue]** Dangerous function eval( used
   - Location: `explored_unused_solutions/Garmin/process_data.py:137`

### MEDIUM Severity (21 bugs)

1. **[Error Handling]** Try block without except clause
   - Location: `qa_test_suite.py:421`

2. **[Error Handling]** Try block without except clause
   - Location: `code_analysis_test.py:49`

3. **[Error Handling]** Try block without except clause
   - Location: `backend/app/tasks.py:18`

4. **[Error Handling]** Try block without except clause
   - Location: `backend/app/tasks.py:52`

5. **[Error Handling]** Try block without except clause
   - Location: `backend/app/tasks.py:93`

6. **[Error Handling]** Try block without except clause
   - Location: `backend/app/api/routes/explainability.py:73`

7. **[Error Handling]** Try block without except clause
   - Location: `backend/app/api/routes/explainability.py:122`

8. **[Error Handling]** Try block without except clause
   - Location: `backend/app/api/routes/explainability.py:207`

9. **[Error Handling]** Try block without except clause
   - Location: `backend/app/api/routes/explainability.py:279`

10. **[Error Handling]** Try block without except clause
   - Location: `backend/app/api/routes/explainability.py:372`

11. **[Error Handling]** Try block without except clause
   - Location: `backend/app/api/routes/explainability.py:478`

12. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/explainability.py:64`

13. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/explainability.py:118`

14. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/explainability.py:199`

15. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/explainability.py:266`

16. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/explainability.py:324`

17. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/explainability.py:448`

18. **[Error Handling]** Try block without except clause
   - Location: `backend/app/services/validation_service.py:86`

19. **[Error Handling]** Try block without except clause
   - Location: `explored_unused_solutions/Garmin/oauth.py:41`

20. **[Error Handling]** Try block without except clause
   - Location: `explored_unused_solutions/Garmin/oauth.py:72`

21. **[Error Handling]** Try block without except clause
   - Location: `explored_unused_solutions/Garmin/oauth.py:115`

## Warnings

1. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:49`

2. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:51`

3. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:58`

4. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:61`

5. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:71`

6. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:188`

7. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:213`

8. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:225`

9. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:282`

10. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:311`

11. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:350`

12. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:377`

13. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:414`

14. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:461`

15. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:462`

16. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:463`

17. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:465`

18. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:466`

19. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:467`

20. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:468`

21. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:470`

22. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:471`

23. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:472`

24. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:475`

25. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:478`

26. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:496`

27. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:499`

28. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:501`

29. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:502`

30. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:507`

31. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:580`

32. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:581`

33. **[Code Quality]** Debug code may be left in: print(
   - Location: `qa_test_suite.py:582`

34. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:31`

35. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:36`

36. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:45`

37. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:145`

38. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:179`

39. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:201`

40. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:222`

41. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:261`

42. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:294`

43. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:319`

44. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:320`

45. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:321`

46. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:324`

47. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:347`

48. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:348`

49. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:349`

50. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:351`

51. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:352`

52. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:355`

53. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:366`

54. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:368`

55. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:372`

56. **[Code Quality]** Debug code may be left in: print(
   - Location: `code_analysis_test.py:377`

57. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:36`

58. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:37`

59. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:38`

60. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:41`

61. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:44`

62. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:50`

63. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:51`

64. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:52`

65. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:58`

66. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:62`

67. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:69`

68. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:79`

69. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:82`

70. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:85`

71. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:102`

72. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:135`

73. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:139`

74. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:144`

75. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:149`

76. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:151`

77. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:154`

78. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:155`

79. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:164`

80. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:166`

81. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:167`

82. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:168`

83. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:169`

84. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:172`

85. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:173`

86. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:185`

87. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:188`

88. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:192`

89. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:202`

90. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:204`

91. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:205`

92. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:206`

93. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:207`

94. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/run_validation_study.py:210`

95. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:29`

96. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:30`

97. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:31`

98. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:36`

99. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:37`

100. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:38`

101. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:39`

102. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:40`

103. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:51`

104. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:52`

105. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:53`

106. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:81`

107. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:82`

108. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:83`

109. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:84`

110. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:89`

111. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:91`

112. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:94`

113. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:95`

114. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:96`

115. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:99`

116. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:110`

117. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:111`

118. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:112`

119. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:120`

120. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:121`

121. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:148`

122. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:149`

123. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:150`

124. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:151`

125. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:155`

126. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:157`

127. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:160`

128. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:161`

129. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:162`

130. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:167`

131. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:178`

132. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:179`

133. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:180`

134. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:191`

135. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:205`

136. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:216`

137. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:217`

138. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:218`

139. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:219`

140. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:223`

141. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:226`

142. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:227`

143. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:228`

144. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:230`

145. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:239`

146. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:240`

147. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:241`

148. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:250`

149. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:257`

150. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:258`

151. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:259`

152. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:261`

153. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:265`

154. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:266`

155. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:269`

156. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:270`

157. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:273`

158. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:274`

159. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:277`

160. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:279`

161. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:282`

162. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:284`

163. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:286`

164. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:292`

165. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:297`

166. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:298`

167. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:299`

168. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:300`

169. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:314`

170. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:315`

171. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:316`

172. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_patterns.py:319`

173. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:53`

174. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:137`

175. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:239`

176. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:240`

177. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:241`

178. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:264`

179. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:265`

180. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:268`

181. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:282`

182. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:285`

183. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:296`

184. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:299`

185. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:304`

186. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:305`

187. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:309`

188. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:320`

189. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:321`

190. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:322`

191. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:344`

192. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:345`

193. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:351`

194. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:352`

195. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:357`

196. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:360`

197. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:366`

198. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:367`

199. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:368`

200. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:369`

201. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:372`

202. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:374`

203. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:377`

204. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:380`

205. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:383`

206. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:385`

207. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:386`

208. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:389`

209. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:391`

210. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:392`

211. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:393`

212. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:404`

213. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:405`

214. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:406`

215. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:412`

216. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:413`

217. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:414`

218. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:416`

219. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:417`

220. **[Code Quality]** Debug code may be left in: print(
   - Location: `scripts/analyze_pmdata_load.py:418`

221. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:27`

222. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:28`

223. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:29`

224. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:30`

225. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:31`

226. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:32`

227. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/__init__.py:33`

228. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/preprocessing.py:6`

229. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/analytics.py:4`

230. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/training.py:6`

231. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/data_ingestion.py:8`

232. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/explainability.py:21`

233. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/explainability.py:581`

234. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/validation.py:12`

235. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/api/routes/data_generation.py:6`

236. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/services/pm_adapter.py:283`

237. **[Code Quality]** Bare except clause - should specify exception type
   - Location: `backend/app/services/preprocessing_service.py:196`

238. **[Code Quality]** Bare except clause - should specify exception type
   - Location: `backend/app/services/preprocessing_service.py:210`

239. **[Code Quality]** Bare except clause - should specify exception type
   - Location: `backend/app/services/validation_service.py:315`

240. **[Code Quality]** Bare except clause - should specify exception type
   - Location: `backend/app/services/validation_service.py:338`

241. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/services/validation_service.py:76`

242. **[Code Quality]** Debug code may be left in: print(
   - Location: `backend/app/services/validation_service.py:115`

243. **[Code Quality]** Bare except clause - should specify exception type
   - Location: `synthetic_data_generation/simulate_year.py:247`

244. **[Code Quality]** Debug code may be left in: print(
   - Location: `synthetic_data_generation/simulate_year.py:438`

245. **[Code Quality]** Debug code may be left in: print(
   - Location: `synthetic_data_generation/simulate_year.py:552`

246. **[Code Quality]** Debug code may be left in: print(
   - Location: `synthetic_data_generation/simulate_year.py:557`

247. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/strava_dat.py:13`

248. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/strava_dat.py:14`

249. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/strava_dat.py:64`

250. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/strava_dat.py:87`

251. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/auth.py:31`

252. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/auth.py:38`

253. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/auth.py:39`

254. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/fetcher.py:42`

255. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/rate_limiter.py:16`

256. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/rate_limiter.py:17`

257. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/strava/main.py:37`

258. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/Garmin/access_data.py:88`

259. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/Garmin/access_data.py:89`

260. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/Garmin/access_data.py:92`

261. **[Code Quality]** Debug code may be left in: print(
   - Location: `explored_unused_solutions/Garmin/process_data.py:213`

262. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/preprocessing.py`

263. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/preprocessing.py`

264. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/preprocessing.py`

265. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

266. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

267. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

268. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

269. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

270. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

271. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

272. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

273. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

274. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

275. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

276. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

277. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

278. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

279. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

280. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

281. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

282. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

283. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

284. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

285. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

286. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

287. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

288. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

289. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

290. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

291. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

292. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/analytics.py`

293. **[Input Validation]** Route accepts JSON but may lack validation
   - Location: `backend/app/api/routes/analytics.py`

294. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

295. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

296. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

297. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

298. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

299. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

300. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

301. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/training.py`

302. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_ingestion.py`

303. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_ingestion.py`

304. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_ingestion.py`

305. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/validation.py`

306. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/validation.py`

307. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/validation.py`

308. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/validation.py`

309. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/validation.py`

310. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/validation.py`

311. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

312. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

313. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

314. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

315. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

316. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

317. **[API Design]** Error response may be missing HTTP status code
   - Location: `backend/app/api/routes/data_generation.py`

318. **[Error Handling]** API calls may lack error handling
   - Location: `frontend/src/api/index.js`

319. **[Data Flow]** Service returns None - ensure callers handle this
   - Location: `backend/app/services/data_generation_service.py`

320. **[Data Flow]** Service returns None - ensure callers handle this
   - Location: `backend/app/services/training_service.py`

321. **[Data Flow]** Service returns None - ensure callers handle this
   - Location: `backend/app/services/preprocessing_service.py`

322. **[Data Flow]** Service returns None - ensure callers handle this
   - Location: `backend/app/services/analytics_service.py`

323. **[Data Flow]** Service returns None - ensure callers handle this
   - Location: `backend/app/services/validation_service.py`

324. **[Configuration]** DEBUG=True found - ensure this is not used in production
   - Location: `backend/app/config.py`

