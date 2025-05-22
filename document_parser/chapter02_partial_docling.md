2

## INTELLIGENT A GENTS

Inwhichwe discuss whatan intelligent entdoes, how it is r elated toits envirnment, ag o how it isevaluated,nd how we mightgo aboutbuilding one. a

## 2.1 I NTR ODUCTION

An agent isanything that canbevie wed as perceiving its environ ment thrugh o sensors and acting upon that environmentthrough effectors . A human agenthaseyes,ears, and otheror gansfor sensors,nd hands,le gs,mouth,and other body parts foref fectors. a A robotic agentsubstitutes cameras and infrared rangefindersforthesensors and various motors fortheef fectors. A software agent hasencodedbit stringssits perceptsndactions. generic agentisdiagrammed a a A inFigure2.1.

Our aim inthis book istodesignagents that do a good jobofacting on theirnvironment. e First, e will be a littlere preciseboutwhat we mean by a good job .Then we will talk about w mo a dif ferent designs forsuccessfulgents-filling inthequestion mark inFigure2.1.W e discuss a some ofthegeneral principles sed inthedesignofagentsthroughout thebook,chief among u which istheprinciple hat agents should t know things. Finally we , show how tocouplean agent toan environmentand describe se veral kindsofenvironments.

## 2.2 H O W A GENTS SHOULD A CT

RA TIONAL AGENT

A rational agent isone that doestheright thing. Ob viouslythis isbetterhandoingthewrong , t thing, butwhat doesitmean? As a first approximation,e w willsaythat theright action isthe one that will causetheagenttobe most successful. hatlea vesus withtheproblemofdeciding T how and when toevaluate theagent'success. s

PERFORMANCE MEASURE

OMNISCIENCE

<!-- image -->

W e use theterm perf ormance measure forthe how -the criteria hatdeterminehow t successfuln agentis.Ob viouslythereisnotone fixed measure suitableorallagents.W e a , f couldasktheagentfora subjecti e opinionofhow v happy itiswithits own performance, but some agents would be unabletoanswer ,and others would deludethemselv es.(Human agents in particular renotoriousor'sourgrapes'-sayingthe y didnotreallyant somethingafter the y a f w areunsuccessfultgetting it.) Therefore,e a w willinsistn an objecti e performancemeasure o v imposedby some authority Inother words,we asoutside observ ersestablishstandard ofwhat . a it means tobe successful nan environment and useit tomeasuretheperformance ofagents. i

As an example,consider the case of an agent that is supposed to vacuum a dirty floor . A plausible erformance measurewould betheamountofdirt cleaned up inasingleight-hour hift. p s A more sophisticatedrformance measurewould factor intheamount ofelectricity nsumed pe co and theamount of noisegenerated as well.A third performancemeasure might gi ve highest marks toan agentthat notonlycleans thefloor quietlynd ef ficiently butalsofinds timetogo a , windsurfingattheweekend. 1

The when ofevaluatingerformance isalsoimportant.fwe measuredhow much dirt the p I agenthad cleaned up inthefirst houroftheday,we would be re wardingthoseagents that start fast (e ven if the y do littleno work latern), and punishing those that work consistently hus, or o .T we want tomeasureperformance overthelongrun, be it an eight-hourhiftra lifetime. s o

W e needtobe carefulodistinguish etweenrationality d t b an omniscience .An omniscient agentknows the actual outcome of its actions,nd can actaccordingly;ut omniscienceis a b impossible inreality Considerthefolloing example:Iam . w walkingalongtheChamps Elys ´es e oneday andIseeanoldfriend across thestreet. hereisno trafc nearbyand I'm nototherwise T fi engaged,so,beingrational, startocrossthestreet.eanwhile,at33,000feet, a car go door I M fallsf fa passing airliner and before Imake it totheother side ofthestreetam o , 2 I flattened. as W Iirrationalcross thestreet?tisunlikelyhat my to I t obituary would read'Idiot attempts tocross

1 There isa dangerhereforthosewho establish erformance measures:you oftengetwhat you askfor . That is, if p you measuresuccess by theamount ofdirt cleaned up,thensome cle veragentisbound tobringina loadofdirt each morning,quickly cleanit up,and geta good performance score. What you reallyant tomeasureishow w cleanthefloor is, butdetermining that ismore difcult thanjust weighingthedirt cleaned up. fi

2 See N. Henderson, 'New doorlatches ur ged forBoeing747 jumbo jets, ' W ashington Post ,8/24/89.

PERCEPT SEQUENCE

IDEAL RA TIONAL AGENT

<!-- image -->

street. Rather ,this points outthat rationality concerned with ' is expected success givenwhat has beenper ceived . Crossing thestreetas rational ecausemost ofthetimethecrossing would be w b successful, nd there was no way Icouldhave foreseen thefallingoor .Note that another agent a d that was equippedwithradarfordetectingallingoorsora steel cagestrong enough torepel f d them would be more successful, utit would notbe any more rational. b

Inother words,we cannot blameanagentfor failing otake into account something it could t notperceie,orforfailing otakean action (suchasrepelling hecar go door)that it isincapable v t t oftaking. But relaxingherequirement ofperfection snotjust a question ofbeingfair toagents. t i The point isthat if we specify that an intelligent entshould alwaysdo what is ag actually theright thing, it will be impossibleodesign an agenttofulfillhis specification-unless e improve the t t w performance ofcrystalalls. b

Insummary,what isrational tany gi ven timedependson fourthings: a

- The performance measurethat definesdegreeofsuccess.
- Everything that theagent hasperceied sofarW ewill call this complete perceptual istory v . h the perceptsequence .
- What theagentknows abouttheenvironment.
- The actions that theagentcanperform.

Thisleadstoa definition of an idealrational agent : For eac h possible per ceptsequence, an ideal r ationalgentshoulddo whateveraction isexpected tomaximizeits performance measure, a on thebasis oftheevidence pr ovidedby theper ceptsequenceand whateverbuilt-in nowledge k theagenthas.

W e need tolookcarefully tthis definition. At first glance, itmight appeartoallo a w an agenttoindulge insome decidedly underintelligent tiities. orexample,ifan agentdoesnot ac v F lookbothways before crossing a busyroad, thenits percept sequencewill nottellt that there is i a lare truck approaching athighspeed.The definitioneems tosaythat it would be OK g s forit to cross theroad.Infact,his interpretation wrong on two counts. First, t would notbe rational t is i tocrosstheroad:theriskofcrossing withoutlookingistoogreat.Second,an ideal rational agentwould have chosenthe'looking' action beforestepping into thestreet, ecauselooking b helpsmaximize theexpectedperformance. Doing actions inordertoobtain useful information isan important part ofrationality d iscoveredindepthinChapter16. an

The notionof an agentismeant to be a toolforanalyzing systems,not an absolute characterization at di videstheworldinto agents and non-agents. Considera clock.Itcan be th thoughtofasjust an inanimate object,ritcan be thoughtofasa simpleagent.As an agent, o most clocksalwaysdo theright action: mo vingtheir hands(ordisplayingigits)ntheproper d i fashion. Clocksarea kindofdegenerate agentinthat their percept sequenceisempty;no matter what happensoutside,heclock'action shouldbe unaf fected. t s

W ell,his is notquite true. If theclock and its owner take a tripromCalifornia oAustralia, t f t theright thing fortheclocktodo would be toturnitself acksixhours.W e do notgetupsetat b ourclocks forfailing odo this becausewe realizehat the y areacting rationally i ven theirack t t ,g l ofperceptualquipment. e 3

3 One oftheauthors still etsa smallthrill hen hiscomputersuccessfully esetstself tdaylighta vingstime. g w r i a s