
2

## Intelligent Agents

In which we discuss what intelligent agents entail, how they relate to their environment, how they are evaluated, and how we might go about building one.

## 2.1 Introduction

An agent is anything that can be viewed as perceiving its environment through sensors and acting upon that environment through effectors. Humans use eyes, ears, and other senses for sensors, while hands, legs, mouth, and other body parts for effectors. A robotic agent substitutes cameras and infrared rangefinders for sensors and various motors for effectors. A software agent encodes bit strings for perceptions and actions; generic agents are diagrammed in Figure 2.1.

Our aim in this book is to design agents that excel in acting on their environment. Initially, we will define precisely what we mean by excellence. Subsequently, we will delve into different designs for successful agents—filling in the gaps in Figure 2.1. We will discuss some general principles underlying agent design throughout the book, among which is the principle that agents should know things. Finally, we will demonstrate coupling an agent with an environment and describe several kinds of environments.

## 2.2 How Agents Should Act

### Rational Agent

A rational agent acts correctly. Obviously, doing the wrong thing is worse than doing the right thing, but what does it mean to act right? As a first approximation, we will say that the right action is the one that causes the agent to be most successful. However, there's a problem: deciding how and when to evaluate its success.

### Performance Measure

**Omniscience**

We use the term performance measure for the criteria that determine how successful an agent is. Obviously, there isn't one fixed measure suitable for all agents. We could ask the agent for a subjective opinion of how happy it is with its performance, but some agents might not be able to respond, and others might exaggerate their satisfaction. (Human agents in particular are notorious for ' sour grapes'--they feel they didn't get what they wanted after being unsuccessful.) Therefore, we insist on an objective performance measure imposed by some authority: we, as outside observers, establish a standard of what it means to be successful in an environment and use it to measure agents' performance.

**Example:** Consider an agent tasked with vacuuming a dirty floor. A plausible performance measure could be the amount of dirt cleaned up in a single eight-hour shift. A more sophisticated measure might factor in electricity consumed, noise generated, and quieter and efficient performance alongside finding time for leisure activities like windsurfing.

Evaluating performance timing is also crucial. Measuring how much dirt the agent cleans up in the first hour of the day rewards early successes but punishes agents that don’t perform consistently over longer periods. To measure performance over the long run—be it an eight-hour shift or lifetime—we want to focus on sustained outcomes.

**Omniscience Distinction**

Distinguishing rationality from omniscience is important. An omniscient agent knows the actual outcome of its actions and acts accordingly; however, omniscience is unrealistic in reality. Consider an example where I walk along Champs Élysées and spot an old friend across the street. There’s no traffic nearby; thus, being rational, I cross the street. However, as I reach 33,000 feet, I narrowly avoid a plane crash before crossing the street; should I be deemed irrational? It’s unlikely my obituary would highlight such an action as foolhardy.

**Performance Measure Hazards**

Establishing performance measures often results in rewarding desired behaviors inadvertently. For instance, if success is measured by cleaning dirt quickly, some agents might consistently leave dirt behind each morning, quickly cleaning it up but still achieving a good score. What we genuinely want to measure is not just dirt cleanliness but effectiveness over sustained periods.

### Perception Sequence

#### Ideal Rational Agent

**Note:** This points out rationality concerning expected success given perceived conditions. Crossing the street rationally might most often succeed due to unforeseen obstacles like a falling door, yet an agent equipped with radar to detect such dangers would be even more rational despite its lack of foresight capabilities.

In summary, rationality depends on four things:

- **Performance Measure:** Defining the degree of success.
- **Perceptual History:** The complete sequence of perceptions.
- **Knowledge about the Environment:** What the agent knows.
- **Actions Capable:** Actions the agent can perform.

For each possible perceptual sequence, an ideal rational agent should perform actions expected to maximize its performance measure based on the perceptual evidence and inherent knowledge.

However, this definition might seem overly simplistic. For example, if an agent fails to look both ways before crossing a busy street, its perceptual sequence won’t imply an impending truck. An ideal rational agent would indeed look first to maximize expected performance, recognizing that gathering information often precedes decisive action. Just like clocks, which appear inert yet reliably adjust their movements based on time, agents should act rationally even if their actions seem simplistic or predictable from an external observer’s perspective.

For instance, a clock, considered an inanimate object, always moves its hands appropriately, aligning with time regardless of external changes. Even though clocks don’t perceive physical alterations like traveling, they adjust internally to reflect the broader environment they're part of. Thus, the essence of rationality isn’t just about external actions but internal coherence within defined operational frameworks.