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

As an example,consider thecaseofan agentthat issupposedtovacuum a dirty floor . A plausible erformance measurewould betheamountofdirt cleaned up inasingleight-hour hift. p s A more sophisticatedrformance measurewould factor intheamount ofelectricity nsumed pe co and theamount of noisegenerated as well.A third performancemeasure might gi ve highest marks toan agentthat notonlycleans thefloor quietlynd ef ficiently butalsofinds timetogo a , windsurfingattheweekend. 1

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

<!-- image -->

## The ideal mapping fr om perceptsequencestoactions

Once we realize hat anagent'beha vior dependsonlyon its percept sequence todate, thenwe can t s describe any particularentby making a table oftheaction it takes inresponse toeachpossible ag percept sequence.(For most agents, this would be a verylonglist-infinite, nfact,nless we i u placea bound on thelength of percept sequenceswe want toconsider ) Such a list iscalled . a mapping from percept sequencestoactions. W e can,inprinciple, nd outwhich mapping fi correctlyescribes an agentby trying outall possible percept sequencesand recording which d actions theagentdoesinresponse. (If theagentusessome randomization inits computations, thenwe would have totry some percept sequences se veral timestogeta good ideaoftheagent' s averagebehavior .)And ifmappingsdescribe agents,hen t ideal mappings describe ideal agents. Specifying hich action an agentoughttotake inr esponsetoanygiven per cept sequence pr ovides w a design foran ideal agent.

This does not mean, of course, thatwe have to create an explicitable with an entry forevery possible percept sequence. Itispossible to define a specificationf themapping o withoutexhaustielyenumerating it.Considera verysimpleagent:thesquare-rootunction v f on a calculator The percept sequenceforthis agentisa sequenceofkeystrokes representing . a number,and theaction istodisplay a number on thedisplay screen. The ideal mapping isthat when thepercept isa positi e number v x ,theright action istodisplay a positi e number v z such that 2 z x ,accurate to,say ,15 decimalplaces. Thisspecification f theideal mapping does o notrequire thedesigner toactuallyonstruct table ofsquareroots. Nor doesthesquare-root c a function have tousea table tobeha ve correctly: igure 2.2shows part oftheideal mapping and F a simpleprogramthat implementsthemapping usingNewton' smethod.

The square-root xample illustrates erelationship etween theideal mapping and an e th b ideal agentdesign, fora veryrestrictedsk. Whereas thetable isverylare,theagentisa nice, ta g compactprogram.Itturns outthat it ispossible todesignnice, compact agents that implement

Figure 2.2 Part oftheideal mapping forthesquare-root roblem(accurateo15 digits),d a p t an correspondingrogramthat implementstheideal mapping. p

|   Percept x | Action z                            |
|-------------|-------------------------------------|
|           1 | 1.000000000000000 1.048808848170152 |

<!-- image -->

Artificial ntelligence: Modern Approach I A by Stuart Russell and Peter Norvig,c 1995 Prentice-Hall, c. In

AUT ONOMY

<!-- image -->

theideal mapping formuch more general situations:ents that can solv e a limitless arietyf ag v o tasks ina limitless arietyfenvironments. Beforewe discuss how v o todo this,e needtolook w atone more requirement that an intelligent entoughttosatisfy ag .

## A utonomy

Thereisone more thingtodealwithinthedefinition ofan ideal rationalgent:the'built-in a knowledge'part. Iftheagent'actions arebasedcompletely on built-in nowledge,suchthat it s k needpay no attention oits percepts,henwe saythat theagentlacks t t autonomy .Forexample, iftheclockmanufacturer was prescientnough toknow e that theclock'owner would be going s to Australiatsome particular ate, thena mechanism couldbe built in to adjust thehands d automatically y sixhoursatjust theright time. Thiswould certainly e successful eha vior ,but b b b theintelligenceems tobelongtotheclock'designer rather thantotheclockitself. se s

An agent'behaviorcan be basedon bothits own s experience and thebuilt-in nowledge k usedinconstructing heagentfortheparticular nvironmentinwhich itoperates. t e A systemis autonomous 4 totheextent thatits behaviorisdetermined by its own experience . Itwould be toostringent, hough, torequire completeautonomy from theword go: when theagenthashad little rno experience,t would have toactrandomlyunless thedesigner gave some assistance. o i So,just asevolution pro vides animals withenough built-in efle xessothat the y cansurvie long r v enough tolearn forthemselv es,it would be reasonable topro videan artificial ntelligent ent i ag withsome initial nowledgeaswellasan ability olearn. k t

Autonomy notonlyfitsinwithourintuition,titisan example ofsound engineering bu practices. n A agentthat operates on thebasis ofbuilt-in ssumptions will onlyoperate successa fully when thoseassumptions hold, and thuslacks flexibilityonsider ,forexample,thelo wly . C dung beetle.fter digging its nest andlaying its eggs,it fetches ball ofdung froma nearbyheap A a toplugtheentrance;ftheball ofdung isremoved from its grasp i en r oute ,thebeetle continues on and pantomimes pluggingthenestwiththenonexistentung ball, nevernoticing thatitis d missing.Evolution hasbuilt an assumption intothebeetle'beha vior ,and when s itisviolated, unsuccessfulehaviorresults. truly autonomous intelligententshouldbe abletooperate b A ag successfully na wide varietyfenvironments,i ven suf ficient timetoadapt. i o g

## 2.3 STR UCTURE OF I NTELLIGENT A GENTS

AGENT PROGRAM

ARCHITECTURE

So farwe have talked aboutagentsby describingheir t behavior -the action that isperformed after any gi ven sequenceof percepts. No w ,we willhave tobite thebullet and talk abouthow theinsides work. The jobofAI istodesignthe agentprogram : a function that implements theagentmapping from percepts toactions. W e assume this program will runon some sort of computingdevice, which we will call the architectur e . Ob viouslytheprogramwe choosehas ,

4 The word 'autonomous'hasalsocome tomean somethinglike 'notundertheimmediatecontrol ofa human,' asin 'autonomouslandvehicle.W e areusingit ina strongerense. ' s

Artificial ntelligence: Modern Approach I A by Stuart Russell and Peter Norvig,c 1995 Prentice-Hall, c. In

SOFTW ARE AGENTS SOFTBO TS

tobeonethat thearchitecturell accept and run.The architectureghtbe aplain computer ,or wi mi it mightinclude special-purposerdwareforcertainasks,uchasprocessingameraimagesor ha t s c filteringudioinput. It mightalso include software that pro vides a degreeofinsulation etween a b thera w computerand theagentprogram,so that we can programata higher le vel.Ingeneral, thearchitecturekes thepercepts from thesensors availableotheprogram,runstheprogram, ma t and feedstheprogram' s action choices totheef fectorssthe y aregenerated. The relationship a among agents, architectures, d programscanbe summed an up asfollos: w

## agent = architectur e + program

Most ofthis book isaboutdesigning agentprograms, although Chapters 24 and 25 dealdirectly withthearchitecture.

Beforewe designan agentprogram,we must have a pretty good ideaof thepossible percepts and actions,hat goalsorperformance measuretheagentissupposedtoachie ve,and w whatsort ofenvironmentit will operate in. Thesecome ina wide variety Figure2.3shows the 5 . basic elements fora selection fagenttypes. o

Itmay come asa surpriseosome readers that we include inourlistfagenttypessome t o programsthat seem tooperate intheentirelyrtificial nvironmentdefined by keyboardinput a e and characterutputon a screen.'Surely ' one might say ,'this isnota real environment, is o , it?'In fact, what matters isnotthedistinction etween 'real' and 'artificial' nvironments, b e butthecomplexityof therelationship mong a thebehaviorof theagent, thepercept sequence generated by theenvironment, and thegoalsthat theagentissupposedtoachie ve. Some 'real' environments areactuallyuite simple.Forexample,a robotdesigned toinspect parts as the y q come by on a conveyer belt can make use of a number of simplifyingssumptions: thatthe a lightingsalwaysjust so,that theonlything on theconveyerbelt will be parts ofa certainind, i k and that there areonlytwo actions-accept thepart ormark it asa reject.

Incontrast, ome s softwar e agents (orsoftware robots or softbots )exist inrich,nlimited u domains. Imaginea softbot designedtofly a flightsimulator fora 747. The simulator isa verydetailed, omplex environment, and thesoftware agentmust choosefrom a wide varietyf c o actions inreal time.Or imaginea softbot designedtoscanonline news sources and show the interesting temstoits customers.To do well, itwillneed some natural languageprocessing i abilities,ill needtolearn what eachcustomerisinterested n, and it will needtodynamically it w i changeits planswhen, forexample,theconnection forone news sourcecrashes or a new one comes online.

Some environmentsblurthedistinction etween 'real' and 'artificial. In theA LIVE b ' environment(Maes etal. ,1994), software agents aregi ven aspercepts a digitized ameraimage c ofa room where a human walksabout.The agentprocesses thecamera image and choosesan action. The environment also displayshecameraimageon a lare display screen that thehuman t g canwatch,and superimposes on theimage a computergraphics rendering ofthesoftware agent. One suchimageisacartoon dog,whichhasbeenprogrammed tomo ve to ward thehuman (unless he points tosendthedog away) and toshakehandsorjump up eagerly when thehuman makes certainestures. g

5 Fortheacronymicallyinded,we call this thePA GE m (Percepts, ctions, Goals, Environment) description.te that A No thegoalsdo not necessarily ave tobe representedithintheagent; theysimplydescribe theperformance measureby h w which theagentdesignwill be judged.

Figure 2.3 Examplesofagenttypesand their PA GE descriptions.

| Agent Type                    | Percepts                               | Actions                                   | Goals                           | Environment                   |
|-------------------------------|----------------------------------------|-------------------------------------------|---------------------------------|-------------------------------|
| Medicaldiagnosis system       | Symptoms, findings, patient' s answers | Questions,ests, t treatments              | Healthypatient, minimizecosts   | Patient, hospital             |
| Satelliteage im analysisystem | Pixels ofvarying intensityolor ,c      | Print a categorization of scene           | Correct categorization          | Imagesfrom orbitingatellite s |
| Part-pickingbot ro            | Pixels ofvarying intensity             | Pickup parts and sort into bins           | Placeparts in correctins b      | Conveyorbelt withparts        |
| Refinery controller           | Temperature, pressureeadings r         | Open,close valves;djust a temperature     | Maximize purity , yield,afety s | Refinery                      |
| InteractiEnglish ve tutor     | Typed words                            | Printxercises, e suggestions, corrections | Maximize student' sscoreon test | Setofstudents                 |

The most famousartificialvironment istheTuring Test environment, inwhich thewhole en pointisthat real and artificial gentsareon equalfooting,uttheenvironmentischallenging a b enoughthat it isverydif ficult for a software agenttodo aswellasa human. Section 2.4describes inmore detailhefactorshat make some environments more demanding thanothers. t t

## Agent programs

W e will be buildingntelligent ents throughout thebook.They will all have thesame skeleton, i ag namely,accepting percepts from an environmentand generatingctions. The early versions of a agentprogramswillhave a verysimpleform (Figure 2.4).Each willuse some internalata d structures hat will be updatedasnew t percepts arri e.These datastructures reoperated on by v a theagent'decision-makingrocedures togenerate an action choice, which isthenpassedtothe s p architecturebe executed. to

Therearetwo things tonoteaboutthis skeleton program. First, ven thoughwe e defined theagentmapping asa function from percept sequences toactions,heagentprogram receies t v onlyasingle percept asits input. It is up totheagenttobuild up thepercept sequenceinmemory , ifitso desires. In some environments, itispossible to be quitesuccessfulithoutstoring w thepercept sequence, and incomplex domains,itisinfeasible ostore thecompletesequence. t

function SKELET ON -AGENT ( per cept ) retur ns action static : memory ,theagent'memory s oftheworld memory U PD ATE -M EMOR Y ( memory,percept ) action C HOOSE -BEST-ACTION ( memory ) memory U PD ATE -M EMOR Y ( memory,action ) retur n action

Figure 2.4 A skeleton agent.On eachin vocation,heagent'memory t s isupdatedtoreflect thenew percept,hebestaction ischosen, and thefact that theaction was takenisalsostored in t memory .The memory persists rom one in vocation tothenext. f

Second,thegoalorperformancemeasureis not partoftheskeleton program. Thisisbecause theperformance measureisapplied externally ojudgethebeha vioroftheagent, and it isoften t possible toachie ve highperformance withoutexplicitnowledge of theperformancemeasure k (see, e.g.,hesquare-root gent). t a

## Wh y notjustlookup theanswers?

Letusstartiththesimplest possibleay we canthink oftowrite theagentprogram-a w w lookup table. Figure 2.5shows theagentprogram.Itoperates by keepinginmemory its entireercept p sequence, and usingit toinde x into table ,which contains theappropriate ction forall possible a percept sequences.

Itisinstructitoconsider why this proposal isdoomed ve tofailure:

- 1. The table neededforsomethingassimpleasan agentthat can onlyplaychesswould be about35 100 entries.
- 2. Itwould takequite a longtimeforthedesigner tobuild thetable.
- 3. The agenthasno autonomy atall,ecause thecalculation fbest actionssentirely uilt-in. b o i b So iftheenvironmentchangedinsome unexpectedway,theagentwould be lost.

function TABLE -DRIVEN -AGENT ( per cept ) retur ns action

static :

per cepts ,a sequence, initially pty em

table ,a table,nde xed by percept sequences,nitially lly specified i i fu

append per cept totheend of action LOOKUP ( per cepts,able t ) retur n action

per cepts

Figure 2.5 An agentbased on a prespecified lookup table.Itkeeps trackof thepercept sequenceand just looksup thebest action.

Artificial ntelligence: Modern Approach I A by Stuart Russell and Peter Norvig,c 1995 Prentice-Hall, c. In

- 4. Even ifwe gave theagenta learningechanism aswell, so that it couldhave a degreeof m autonomy,it would takefore vertolearn theright valueforall thetable entries.

Despiteall this,ABLE T -DRIVEN -AGENT does do what we want:it implementsthedesired agent mapping.It isnotenough tosay ,'It can' tbe intelligent;epoint istounderstand why an agent ' h that reasons (asopposedtolooking things up ina table)ando even bettery avoiding thefour c b dra wbacks listedere. h

## An example

At thispoint, itwillbe helpful to consider a particular nvironment, so thatour discussion e can become more concrete. Mainly becauseofits familiarity nd becauseitin volv esa broad ,a rangeofskills, e w willlookatthejobofdesigning an automatedtaxi dri ver . W e shouldpoint out,beforethereader becomes alarmed, that such a systemiscurrentlyomewhat beyond the s capabilities existingechnology although mostofthecomponentsareavailablensome form. of t , i 6 The full dri vingtaskisextremely open-ended -there isno limit tothenovelcombinations of circumstanceshat canarise (whichisanother reasonwhy we choseit asa focusfordiscussion). t

W e must first think aboutthepercepts, ctions,oalsand environmentforthetaxi. They a g aresummarizedinFigure 2.6and discussed inturn.

| Agent Type   | Percepts                                     | Actions                                     | Goals                                                 | Environment                                 |
|--------------|----------------------------------------------|---------------------------------------------|-------------------------------------------------------|---------------------------------------------|
| Taxidrier v  | Cameras, speedometerGPS, , sonarmicrophone , | Steeraccelerate, , brake, talk to passenger | Safe, fast,egal, l comfortablerip, t maximize profits | Roads,other trafc,pedestrians, fi customers |

The taxi will need toknow where it is, what else ison theroad, and how fast it isgoing. Thisinformation can be obtained from the percepts pro videdby one or more controllable V T cameras, thespeedometerand odometer .To control thevehicle properly especially n curv es, it , , o shouldhave an accelerometer; t will also needtoknow i themechanical state ofthevehicle,oit s will needtheusualarray ofengineand electricalstemsensors. Itmighthave instrumentshat sy t arenotavailableotheaveragehuman dri ver:a satellite obal positioning ystem(GPS) togi ve t gl s it accurateositionnformationithrespect toan electronic ap; orinfraredrsonarsensors to p i w m o detect distancesoothercarsand obstacles.inally itwill need a microphoneorkeyboardfor t F , thepassengers totellt their destination. i

The actions available oataxi dri verwill bemore orless thesame onesavailable oahuman t t dri ver:control overtheenginethroughthegaspedaland control oversteeringnd braking. In a addition, t will need output toa screen orvoicesynthesizer otalk back tothepassengers,nd i t a perhapssome way tocommunicatewithother vehicles.

6 See page26 fora description fan existingri vingrobot, orlookattheconference proceedingsn Intelligenthicle o d o Ve and Highway Systems(IVHS).

CONDITION-A CTION RULE

What perf ormance measure would we like ourautomateddri vertoaspire to?Desirable qualities nclude getting tothecorrectestination;nimizingfuel consumptionand wear and i d mi tear;inimizingthetrip timeand/or cost; minimizing violations ftrafc la ws and disturbances m o fi toother dri vers; maximizingsafety and passenger comfort; maximizingprofits. Ob viously some , ofthese goalsconflict,o there will be trade-of sin volv ed. s f

Finally werethis areal project, e would needtodecide whatkindofdri ving , w envir onment thetaxi will face. Shouldit operate on local roads, oralsoon freeays? w W ill it be inSouthern California, here snow w isseldoma problem, orinAlaska, where it seldomisnot?W ill it always be dri vingon theright,rmightwe want it tobe flexible enough todri ve on theleft incasewe o want tooperate taxis inBritain orJapan? Ob viouslythemore restrictedeenvironment, the , th easier thedesignproblem.

No w we have to decidehow to builda realprogram toimplement themapping from percepts toaction. W e will find that diferentspects ofdri vingsuggest dif ferentypesofagent f a t program.W e will consider fourtypes ofagentprogram:

- Simplerefle x agents
- Agentsthat keeptrack oftheworld
- Goal-based agents
- Utility-basedents ag

## Simple reflex agents

The option ofconstructing n explicit ookuptable isoutofthequestion.he visual input from a l T a single camera comes inattherate of50 me gabytes persecond(25framespersecond, 1000 1000 pix elswith8 bits ofcolor and 8 bits ofintensity nformation). o thelookuptable foran i S hourwould be 2 60 60 50 M entries.

Ho wever ,we can summarizeportions ofthetable by noting certainommonly c occurring input/out utassociations. orexample,ifthecarinfront brakes, and its brakelightsome p F c on, thenthedri vershouldnotice this and initiateaking. Inother words,some processingsdoneon br i thevisual input toestablish heconditione call 'The carinfront isbraking';henthis triggers t w t some established onnection intheagentprogramtotheaction 'initiateaking'. W e call such c br a connection a condition-action ule r 7 written as

## if car -in-fr nt-is-bring o ak then initiate-br ing ak

Humans alsohave man y suchconnections, ome ofwhich arelearned responses (asfordri ving) s and some ofwhich areinnate refle xes (suchasblinking when somethingapproaches theeye). Inthecourseofthebook,we will seese veral dif ferent ways inwhich suchconnections can be learned and implemented.

Figure2.7gi ves thestructure f a simplerefle x agentinschematic form,showing how o thecondition-actionles allo theagenttomake theconnection from percept toaction. (Do ru w notworry ifthis seems triial; itgetsmore interesting hortly ) W e use rectanglesodenote v s . t

7 Also called situation-action ules productions r , ,or if-then rules . The last termisalsousedby some authors for logicalmplications,we will avoidit altogether i so .

Figure 2.7 Schematicdiagramofa simplerefle x agent.

<!-- image -->

function SIMPLE -REFLEX -AGENT ( per cept ) retur ns static : rules ,a set ofcondition-action les ru action

state I NTERPRET -I NPUT ( per cept )

rule RULE -M ATCH ( state, ules r )

action RULE -ACTION [ rule ]

retur n action

Figure 2.8 A simplerefle x agent.Itworks by finding a rulewhose condition matchesthe current situation asdefined by thepercept)nd thendoingtheaction associated iththat rule. ( a w thecurrent internal tate oftheagent'decision process,nd ovalstorepresenthebackground s s a t information used in theprocess.The agentprogram,which isalsoverysimple, isshown in Figure2.8.The I NTERPRET -I NPUT function generates an abstractedescription f thecurrent d o state from thepercept,nd theR ULE -M ATCH a function returnshefirst rule intheset ofrules that t matchesthegi ven state description. lthoughsuchagents can be implementedveryef ficiently A (seeChapter10), their rangeofapplicability verynarro w ,aswe shall see. is

## Agents thatkeep trackoftheworld

The simplerefle x agentdescribed beforewillwork onlyifthecorrect decision can be made on thebasis of thecurrent percept. Ifthecarinfront isa recent model,and has thecentrally mounted brakelight now required intheUnitedStates,henitwillbe possible totell ifitis t brakingfrom a single image. Unfortunately oldermodels have dif ferent configurationsftail , o

INTERNAL STATE

GOAL

SEARCH

PLANNING

lights, rakelights, nd turn-signalghts, nd it isnotalwayspossibleotellf thecarisbraking. b a li a t i Thus,even forthesimplebrakingrule, our dri verwillhave tomaintain some sort of inter nal state inordertochoosean action. Here,theinternal tate isnottooextensie-it just needsthe s v pre viousframefrom thecameratodetect when two redlightsttheedgeofthevehicle go on or a of fsimultaneously .

Considerthefolloing more obviouscase:from timetotime,thedri verlooksin the w rear -vie w mirror tocheckon thelocations fnearbyvehicles.hen o W thedri verisnotlooking in themirror ,thevehiclesnthenextlanearein visiblei.e.,estatesnwhich the y arepresent and i ( th i absent areindistinguishabl butinorder todecideon a lane-changeaneuver ,thedri verneeds e); m toknow whetherornotthe y arethere.

The problemillustratedthis example arisesecausethesensors do notpro videaccess to by b thecompletestate oftheworld.Insuchcases, theagentmay needtomaintain some internal tate s informationnordertodistinguish etweenworldstateshat generate thesame perceptualnput i b t i butnonethelessresignificantly if ferent. Here,'significantly if ferent' means that dif ferent a d d actions areappropriate nthetwo states. i

Updatingthis internal tatenformationstimegoesby requireswo kindsofknowledgeto s i a t be encodedintheagentprogram.First, e needsome informationbouthow theworldevolv es w a independentlyftheagent-forexample,that an overtaking cargenerallyill be closer behind o w thanit was a moment ago.Second,we needsome informationbouthow theagent'own actions a s af fect theworld-for example,that when theagentchangeslanes totheright,here isa gap (at t least temporarily) nthelaneit was inbefore, orthat after dri vingforfive minutesnorthbound i on thefreeay one isusually aboutfive milesnorth ofwhere one was five minutesago. w

Figure2.9gi ves thestructuref therefle x agent,showing how o thecurrent percept is combinedwiththeoldinternal tate togenerate theupdateddescription fthecurrent state.he s o T agentprogramisshown inFigure 2.10. The interestingrt isthefunction PD ATE -STATE ,which pa U isresponsibleorcreating thenew f internaltate description. s s A wellas interpretingenew th percept inthelightfexistingnowledgeaboutthestate, t usesinformationbouthow theworld o k i a evolv estokeeptrack oftheunseenparts oftheworld, andalso must know aboutwhat theagent' s actions do tothestate oftheworld.Detailed examplesappearinChapters 7 and 17.

## Goal-basedagents

Kno wing aboutthecurrent state oftheenvironmentisnotalwaysenough todecidewhat todo. Forexample,ata roadjunction, hetaxi canturnleft, ight,rgo straight n.The right decision t r o o dependson wherethetaxi istrying togetto.Inother words,aswellasacurrenttateescription, s d theagentneedssome sort of goal information, hich describesituations hat aredesirablew t forexample,beingatthepassenger'destination. he agentprogram can combine this with s T information abouttheresultsf possible actions (thesame informations was used toupdate o a internaltate intherefle x agent) inordertochooseactions that achie ve thegoal.Sometimes s this will be simple, when goalsatisfaction sultsmmediately from a single action;ometimes, re i s it will be more trick ,when y theagenthastoconsider longsequences oftwists and turns tofind a way toachie ve thegoal. Search (Chapters 3 to5)and planning (Chapters 11 to13)arethe subfields ofAI devotedtofindingaction sequences that do achiee theagent'goals. v s

Figure 2.9 A refle x agentwithinternal tate. s

<!-- image -->

function R EFLEX -AGENT -W ITH -STATE ( per cept ) retur ns action static : state ,a description fthecurrent worldstate o rules ,a set ofcondition-action les ru

state U PD ATE -S TATE ( state, er cept p ) rule RULE -M ATCH ( state, ules r ) action RULE -ACTION [ rule ] state U PD ATE -S TATE ( state, ction a ) retur n action

Figure 2.10 A refle x agentwithinternaltate. Itworks by finding a rulewhose condition s matchesthecurrent situation asdefined by thepercept and thestored internaltate)nd then ( s a doingtheaction associatediththat rule. w

Noticethat decision-making ofthis kindisfundamentally dif ferent from theconditionaction rules described earlier inthat itin volv es consideration f thefuture-both'What , o will happen ifI do such-and-such?' and 'W ill that make me happy?' Intherefle x agentdesigns, this informationsnotexplicitly sed,becausethedesigner hasprecomputedthecorrect action i u forvarious cases.The refle x agentbrakeswhen itseesbrakelights. A goal-based agent, in principle, ouldreasonthat ifthecarinfront hasits brakelightsn,itwillslo w c o down. From theway theworldusually evolv es, theonlyaction that will achiee thegoalofnothittingther v o carsistobrake. Althoughthegoal-based agentappears less ef ficient,t isfar more flexible. Ifit i startsorain, theagentcan updateits knowledgeofhow t ef fecti elyits brakeswill operate;his v t will automatically auseall ofthereleantbeha viors tobe alteredosuit thenew c v t conditions. or F therefle x agent, on theother hand,we would have tore write a lare number ofcondition-action g

UTILITY

rules. Of course, thegoal-based agentisalsomore flexible withrespect toreaching dif ferent destinations.mply by specifying new Si a destination, can getthegoal-based agenttocome we up witha new behavior . The refle x agent'rules forwhen s toturnand when togo straight ill w onlywork fora single destination;e y must all be replaced togo somewhere new . th

Figure2.11shows thegoal-based agent' structure.hapter13 contains detailedgent s C a programsforgoal-based agents.

Figure 2.11 An agentwithexplicit oals. g

<!-- image -->

## Utility-based gents a

Goalsalonearenotreallynoughtogenerate high-quality ehavior .Forexample,there areman y e b action sequencesthat willgetthetaxi toits destination,ereby achie vingthegoal, butsome th arequickersafermore reliable, rcheaperthanothers. Goalsjust pro videa crudedistinction , , o between'happy'and 'unhappy'states, hereasa more general performancemeasureshould w allo a comparisonofdif ferent worldstatesorsequences of states)ccording toexactly how w ( a happy the y would make theagentifthe y couldbe achie ved. Because'happy'doesnotsound veryscientific, hecustomaryterminology istosaythat if one worldstate ispreferredoanother t t , thenit hashigher utility fortheagent. 8

Utilitysthereforefunction that maps a stateontoa real number,which describeshe i a 9 t associatedegreeofhappiness. A d completespecification ftheutility unction allos rational o f w decisionsntwo kindsofcases where goals have trouble.irst, hen there areconflictingoals, i F w onlysome ofwhichcanbeachie ved (for example,speedand safety), heutility unctionpecifies t f s theappropriate rade-of .Second,when there arese veral goalsthat theagentcan aim for ,none t f

8 The word 'utility'rerefers to'thequalityfbeinguseful, nottotheelectric ompany orwaterworks. he o ' c

9 Or sequenceofstates, fwe aremeasuringtheutility fan agentoverthelongrun. i o

ofwhichcanbeachie ved withcertaintytility ro vides a way inwhich thelikelihood fsuccess ,u p o canbe weighedup against theimportance ofthegoals.

In Chapter16,we show that any rationalgentcan be described as possessing a utility a function.n agent that possessesn A a explicit utili yfuncti n t hereforeanmake rational ecisions, t o c d butmay have tocompare theutilities hie ved by dif ferent courses ofactions.oals, although ac G cruder enabletheagenttopickan action right away , ifitsatisfieshegoal. In some t cases, moreover ,a utility unctionanbe translated nto a setofgoals, suchthat thedecisionsade by f c i m a goal-based agentusingthosegoalsareidentical othosemade by theutility-b edagent. t as

The overalltility-based entstructure ppears inFigure 2.12. Actualutility-b edagent u ag a as programsappearinChapter5,where we examine game-playing programsthat must make fine distinctionsong am various board positions; nd in Chapter17, where we a tackle thegeneral problemofdesigning decision-makinggents. a

Figure 2.12 A completeutility-based ent. ag

<!-- image -->

## 2.4 ENVIR ONMENTS

Inthis section and intheexercisesttheend ofthechapteryou will seehow a , tocouplean agent toan environment.Section 2.3introduced se veral dif ferent kindsof agents and environments. Inall cases, however ,thenature oftheconnection betweenthem isthesame: actions aredone by theagenton theenvironment, which inturnpro videspercepts totheagent.First,e w will describe thedif ferent types ofenvironments and how the y af fect thedesignofagents. Then we will describe environmentprogramsthat canbe usedastestbedsoragentprograms. f

ACCESSIBLE

DETERMINISTIC

EPISODIC

STATIC

SEMID YNAMIC

DISCRETE

## Properties ofenvir onments

Environments come inse veral flavors. The principal istinctions be made areasfollos: d to w

## Accessible vs. inaccessible .

Ifan agent'sensoryapparatus gi vesitaccesstothecompletestate of theenvironment, s thenwe saythat theenvironment isaccessible othat agent. An t environmentisef fecti ely v accessiblefthesensors detect all aspects that arereleanttothechoiceof action. An i v accessible nvironment isconvenient because theagent neednotmaintain any internal tate e s tokeeptrack oftheworld.

## Deterministic vs. nondeterministic .

Ifthenextstate oftheenvironmentiscompletely determined by thecurrent state and the actions selectedy theagents, thenwe b saytheenvironmentisdeterministic.principle, In an agentneed notworryaboutuncertainty nan accessible, eterministic vironment. If i d en theenvironmentisinaccessible, wever ,thenit may ho appear tobe nondeterministic. is Th isparticularlyueiftheenvironmentiscomplex,making it hardtokeep track ofall the tr inaccessible spects.hus,it isoften betterothink ofan environmentasdeterministic a T t or nondeterministic fr om thepoint ofvie w oftheagent .

## Episodic vs. nonepisodic .

Inanepisodic environment, theagent'experience is di videdinto 'episodes. Each episode s ' consistsftheagentperceiingand thenacting. The qualityfits action dependsjust on o v o theepisodeitself, ecausesubsequent episodes do notdepend on what actions occurin b pre viousepisodes. Episodic environments aremuch simpler becausetheagentdoesnot needtothink ahead.

## Static vs. dynamic .

Iftheenvironmentcanchangewhilean agentisdeliberating, enwe saytheenvironment th isdynamic forthat agent; otherwise it isstatic. taticnvironments areeasytodealwith S e becausetheagentneed notkeep lookingattheworldwhileitisdeciding on an action, norneeditworryaboutthepassageoftime.Iftheenvironmentdoesnotchangewiththe passageoftimebuttheagent'performance scoredoes,thenwe saytheenvironmentis s semidynamic .

## Discr ete vs. continuous .

Ifthere area limited number ofdistinct,earlyefined percepts and actions we cl d saythat theenvironmentisdiscrete. hessisdiscrete-there rea fixed number ofpossibleo ves C a m on eachturn. Taxidri vingiscontinuous-thespeedand locationfthetaxi and theother o vehiclesweep througha rangeofcontinuous values. 10

W e will seethat dif ferentnvironmenttypesrequire somewhat dif ferent agentprogramstodeal e withthem ef fecti ely .It will turnout, asyou mightexpect, that thehardest caseis v inaccessible , nonepisodic dynamic , ,and continuous .Italsoturns outthat most real situations reso complex a that whetherthe y are really deterministica moot point; forpractical urposes, the y must be s p treatedsnondeterministic. a

10 At a fine enough le velof granularityven thetaxidri vingenvironmentisdiscrete, ecausethecamera image is ,e b digitized oyield discreteixel values. But any sensiblegentprogram would have toabstractbovethis le vel, up toa t p a a le velofgranularity hat iscontinuous. t

Figure 2.13lists heproperties fanumber offamiliar nvironments. Notethat theanswers t o e can change dependingon how you conceptualize heenvironments and agents.For example, t pokerisdeterministic ftheagentcan keep trackof theorderof cardsinthedeck,butitis i nondeterministic fitcannot.Also,man y environments areepisodic athigherle velsthanthe i agent' indi vidual actions. For example,a chesstournamentconsistsf a sequenceof games; s o eachgame isan episode, because(byand lare)thecontrib tion ofthemo vesinone game tothe g u agent'overall performanceisnotaf fected by themo ves inits nextgame. s On theotherhand, mo veswithin a single game certainly nteract,theagentneedstolookaheadse veral mo ves. i so

| Environment                                                                                                                                                                      | Accessible                     | Deterministic                 | Episodic                     | Static                               | Discrete                           |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|-------------------------------|------------------------------|--------------------------------------|------------------------------------|
| Chesswitha clock Chesswithout a clock Poker Backgammon Taxidriing v Medicaldiagnosisystem Image-analysis system Part-pickingbot ro Refinery controller InteractiEnglish ve tutor | Yes Yes No Yes No No Yes No No | Yes Yes No No No No Yes No No | No No No No No No Yes Yes No | Semi Yes Yes Yes No No Semi No No No | Yes Yes Yes Yes No No No No No Yes |

Figure 2.13

Examples ofenvironments and their characteristics.

## En vir onment programs

The generic environment programinFigure 2.14illustrates ebasic relationshiptweenagents th be andenvironments. Inthis book,we will find it convenient forman y oftheexamplesand exercises tousean environmentsimulator that follos this program structure. he simulatorakes one or w T t more agents asinput andarrangesorepeatedly i veeachagent theright perceptsndreceieback t g a v an action. The simulatorhenupdates theenvironmentbasedon theactions, nd possibly other t a dynamic processes intheenvironmentthat arenotconsidered tobe agents(rain,orexample). f The environmentisthereforeefined by theinitial tate and theupdatefunction.f course, an d s O agentthat works ina simulatorughtalsotowork ina real environmentthat pro vides thesame o kindsofpercepts and accepts thesame kindsofactions.

The R UN -ENVIR ONMENT procedure correctly xercisesheagents inan environment. For e t some kindsofagents, suchasthose that engageinnaturalanguage dialogue,t may be suf ficient i simplytoobserv e their beha vior To getmore detailednformationboutagentperformance,e . i a w insertome performance measurementcode.The function R UN -EVAL -ENVIR ONMENT s ,shown in Figure2.15, doesthis; itapplies a performance measuretoeachagentand returns a listf the o resulting cores. The s scor es variableeepstrack ofeachagent'score. k s

Ingeneral, theperformancemeasurecan depend on theentire sequenceofenvironment statesenerated during theoperationftheprogram.Usually ,however ,theperformance measure g o

Artificial ntelligence: Modern Approach I A by Stuart Russell and Peter Norvig,c 1995 Prentice-Hall, c. In

```
,agents, termination )
```

```
procedure RUN -ENVIR ONMEN T( state, U PD ATE -F N inputs : state ,theinitial tateftheenvironment s o U PD ATE -F N ,functionomodify theenvironment t agents ,a setofagents termination ,a predicateotest when we aredone t repeat f or each agent in agents do PERCEPT [ agent ] G ET-PERCEPT ( agentstate , ) end f or each agent in agents do A CTION [ agent ] PROGRAM [ agent ](P ERCEPT [ agent ]) end state U PD ATE -F N ( actions, gents,tate a s ) until terminationtate ( s )
```

Figure 2.14 The basic environment simulatorrogram.Itgi veseachagentits percept,ets an p g action from eachagent, and thenupdates theenvironment.

```
function RUN -EVAL -ENVIR ONMEN T( state, U PD ATE -F N ,agents, termination, PERFORMANCE -FN) retur ns scor es local variables : scor es ,a vector thesame size as agents ,all 0 repeat f or each agent in agents do PERCEPT [ agent ] G ET-PERCEPT ( agentstate , ) end f or each agent in agents do A CTION [ agent ] PROGRAM [ agent ](P ERCEPT [ agent ]) end state U PD ATE -F N ( actions, gents,tate a s ) scor es PERFORMANCE -FN( scor es, agents,tate s ) until terminationtate ( s ) retur n scor es /* change */
```

Figure 2.15 An environmentsimulator programthat keepstrack oftheperformance measure foreachagent.

works by a simpleaccumulation usingeitherummation,averaging, ortaking a maximum. s For example,iftheperformancemeasure fora vacuum-cleaning agentisthetotal amount of dirt cleaned ina shift, scor es will just keeptrack ofhow much dirt hasbeencleaned up sofar .

RUN -EVAL -ENVIR ONMENT returns theperformancemeasure fora a single environment, defined by a single initialatend a particulardatefunction.sually ,an agentisdesigned to st a up U

Artificial ntelligence: Modern Approach I A by Stuart Russell and Peter Norvig,c 1995 Prentice-Hall, c. In

## ENVIRONMENT CLASS

work inan envir onment class ,a whole setofdif ferent environments. Forexample,we design a chessprogram toplayagainst any ofa wide collection fhuman o and machine opponents.If we designed it fora single opponent, we mightbe abletotakeadvantageofspecific weaknesses inthat opponent, butthat would notgi ve us a good program forgeneral play . Strictly peaking, s inordertomeasure theperformanceof an agent, we need tohave an environmentgenerator that selectsarticular nvironments (withcertainikelihoods)which toruntheagent. W e are p e l in theninterested n theagent' averageperformanceovertheenvironmentclass.Thisisfairly i s straightforwardimplementfora simulated environment, and Exercises 2.5to2.11takeyou to throughtheentire developmentofan environment and theassociated easurementprocess. m

A possible confusion arises betweenthestate variablentheenvironmentsimulator and i thestate variablentheagentitself see R EFLEX i ( -AGENT -W ITH-STATE ).As a programmer implementingboththeenvironmentsimulator and theagent, it istempting toallo w theagenttopeek attheenvironmentsimulator' state variable.histemptationust be resisted tall costs! The s T m a agent' version of thestate must be constructedrom its percepts alone, withoutaccesstothe s f completestate information.

## 2.5 SUMMAR Y

Thischapter hasbeen somethingofa whirlwindtourofAI,which we have concei ved ofasthe science ofagentdesign. The majorpoints torecallreasfollos: a w

- An agent issomethingthat perceiesand acts inan environment. W e splitn agentinto v a an architectured an agentprogram. an
- An ideal agent isone that alwaystakes theaction that isexpectedtomaximize its perfor -mance measure, gi ven thepercept sequenceit hasseenso far .
- An agentis autonomous totheextent that its action choices dependon its own experience, rather thanon knowledgeoftheenvironment that hasbeenbuilt-in y thedesigner b .
- An agentprogram maps from a percept toan action,hileupdating an internal tate. w s
- Thereexists avarietyfbasic agent programdesigns,epending on thekindofinformation o d made explicit ndusedinthedecisionrocess.he designs varyinef ficienc y,compactness, a p T and flexibility The appropriateesignof theagentprogram dependson thepercepts, . d actions,oals, and environment. g
- Reflex agents respondimmediately topercepts, goal-basedagents actso that the y will achie ve theiroal(s), nd g a utility-based gents a trytomaximize their own 'happiness. '
- The processof making decisions by reasoning withknowledge iscentral to AI and to successfulgentdesign. Thismeans that representing nowledgeisimportant. a k
- Some environments aremore demanding thanothers. Environments that areinaccessible, nondeterministic, nepisodic, ynamic,and continuous arethemost challenging. no d

## B IBLIOGRAPHICAL AND H ISTORICAL N O TES

The analysisfrational genc y asa mapping from percept sequences toactions probably stems o a ultimately rom theef fort toidentify ational eha vior intherealmofeconomicsand other forms f r b ofreasoning underuncertainty co veredinlaterhapters)nd from theef forts ofpsychological ( c a behaviorists uchasSkinner (1953) toreducethepsychology ofor ganismsstrictlyinput/output s to orstimulus/responseppings.The advancefrom behaviorism tofunctionalism npsychology , ma i whichwas atleast partly dri ven by theapplication fthecomputermetaphortoagents (Putnam, o 1960;Lewis,1966),introduced theinternal tate oftheagentinto thepicture.he philosopher s T DanielDennett(1969; 1978b)helpedtosynthesizehese vie wpointsinto a coherent 'intentional t stance' to ward agents. A high-le el, abstract erspecti on agenc y is also taken within theworld v p ve ofAI in(McCarthyand Hayes,1969).JonDoyle (1983)proposedthat rational gentdesignis a thecoreofAI,and would remainasits missionwhileother topics inAI would spinof ftoform new disciplines.rvitz Ho etal. (1988)specifically uggest theuseofrationality ncei ved asthe s co maximization ofexpectedutility sa basis forAI. a

The AI researcher ndNobel-prize-winningonomist Herb Simon dre w aclear distinction a ec betweenrationalityderresource limitationsroceduralationality) d rationalitymaking un (p r an as theobjecti elyrational hoice (substantirationality) imon,1958).Cherniak(1986)explores v c ve (S theminimalle velofrationality ededtoqualifynentitysanagent. Russell andW efald (1991) ne a a dealexplicitly iththepossibilityusinga variety ofagentarchitectures. w of Dung Beetle Ecology (Hanskiand Cambefort, 1991)pro videsa wealthofinterestingformationn thebehavior in o ofdung beetles.

- 2.1 What isthedif ference betweena performance measureand a utility unction? f
- 2.2 Foreachoftheenvironments inFigure2.3, determine what typeofagentarchitecture s i most appropriate tableookup, simplerefle x,goal-based orutility-based). ( l
- 2.3 Choose a domain thatyou arefamiliarith,and writea PA GE w description f an agent o fortheenvironment. Characterize heenvironmentasbeingaccessible, eterministic, isodic, t d ep static, nd continuous ornot.What agentarchitecturebest forthis domain? a is
- 2.4 While dri ving, which isthebestpolic? y
- a . Always putyourdirectionalinker on before turning, b
- b . Neveruseyourblinker ,
- c . Look inyourmirrors and useyourblinker onlyifyou observ e a carthat canobserv e you?

What kindofreasoning didyou needtodo toarrie atthis polic (logical, oal-based, rutilityv y g o based)?What kindofagentdesignisnecessary tocarryoutthepolic (refle x,goal-based,r y o utility-b ed)? as

Artificial ntelligence: Modern Approach I A by Stuart Russell and Peter Norvig,c 1995 Prentice-Hall, c. In

## EXERCISES

<!-- image -->

The folloing exercisesll concerntheimplementation ofan environmentand setofagents in w a thevacuum-cleaner world.

- 2.5 Implementa performance-measuring nvironment simulatororthevacuum-cleaner world. e f Thisworldcanbe described asfollos: w
- Percepts : Each vacuum-cleaner agentgetsa three-element ercept vector on eachturn. p The first element, a touchsensorshouldbe a 1 if themachinehasbumped , into something and a 0 otherwise.he secondcomes from a photosensor underthemachine,which emits T a 1 if there isdirthere and a 0 otherwise.he third comes from an infraredensorwhich t T s , emitsa 1 when theagentisinits home location, nd a 0 otherwise. a
- Actions : Therearefive actions available: o forward, turnright by 90 g ,turnleft by 90 , suckup dirt,nd turnof f. a
- Goals :The goalforeachagentistoclean up and go home. To be precise, heperformance t measure willbe 100 points foreach pieceof dirt vacuumed up,minus 1 pointforeach action taken, and minus 1000 points if it isnotinthehome locationhen it turns itself f f. w o
- En vir onment : The environmentconsists of a gridof squares.Some squarescontain obstacleswalls and furniture)dother squares areopenspace. Some ( an oftheopensquares contain dirt.ach 'go forward' action mo vesone square unless there isan obstaclenthat E i square, inwhich casetheagentstays where it is, butthetouchsensor goeson.A 'suckup dirt' action alwayscleans up thedirt. A 'turn of f' command endsthesimulation.

W e canvarythecomplexity oftheenvironmentalongthree dimensions:

- Room shape :Inthesimplest case, theroom isan n n square, forsome fixed n .W e can make it more dif ficult by changingtoa rectangular-shaped, orirreularly shapedroom, ,L g ora seriesfrooms connected by corridors. o
- Furnitur e : Placing furniture ntheroom makes it more complex thanan empty room. To i thevacuum-cleaning agent, a pieceof furniture annotbe distinguished rom a wallby c f perception; othappearasa 1 on thetouchsensor b .
- Dirtplacement : Inthesimplest case, dirt isdistribeduniformly aroundtheroom. But ut it ismore realisticrthedirt topredominate incertainocations, uchasalonga hea vily fo l s tra velled pathtothenextroom,orinfront ofthecouch.
- 2.6 Implementatable-lookup gentforthespecialaseofthevacuum-cleaner worldconsisting a c ofa 2 2 gridofopen squares,nwhich atmost two squares will contain dirt.he agentstarts i T intheupperleft cornerfacing totheright.ecall that a table-lookup gentconsistsfa table of , R a o actions inde xed by a percept sequence.Inthis environment, theagentcan alwayscompleteits taskinnineorfe wer actions (four mo ves, three turns,nd two suck-ups),othetable onlyneeds a s entriesorpercept sequencesup tolength nine.At each turn, there areeight possible percept f vectors,o thetable will be ofsize s 9 i =1 8 i = 153,391,688. Fortunately we can cutthis down , by realizing hat thetouchsensor and home t sensor inputs arenotneeded; we canarrange sothat theagentneverbumps intoa walland knows when ithasreturned home. Then there areonly two releantpercept vectors,0? and ?1?,and thesizeofthetable isatmost v ? 9 i =1 2 i = 1022. Run theenvironmentsimulator on thetable-lookup gentinall possible worlds(ho w a man y are there?).ecordits performance scoreforeachworldand its overallveragescore. R a

- 2.7 Implementanenvironment for a n m rectangular oom,whereeachsquare hasa5% r chance ofcontainingirt,nd d a n and m arechosenatrandom from therange8 to15,inclusi e. v
- 2.8 Designand implementa purerefle x agentfortheenvironmentof Exercise 2.7,ignoring therequirement ofreturningome, and measureits performance. Explainwhy h itisimpossible tohave a refle x agentthat returnsome h and shuts itself f f.Speculate on what thebest possible o refle x agentcoulddo.What pre vents a refle x agentfrom doingverywell?
- 2.9 Designand implementse veral agents withinternal tate.easure their performance. Ho w s M close do the y come totheideal agentforthis environment?
- 2.10 Calculate thesizeof thetable fora table-lookupgentinthedomain of Exercise 2.7. a Explainyourcalculation. ou neednotfillintheentriesorthetable. Y f
- 2.11 Experimentwithchangingtheshapeand dirt placementof theroom, and withadding furniture.easure your agentsinthesenew M environments.Discusshow their performance mightbe improved tohandlemore complex geographies.