"""Authored seat distinctions, not acceptance oracles and not a second Core.

IDs resolve exclusively through the pinned canonical registry. These contracts
describe HOW each seat works. They do not award maturity; separate executable
domain scenarios and independent expected decisions are required for acceptance.
"""
import copy
import re
from .role_specs import SEAT_SKILLS

# ID | professional decision | failure modes | competing hypotheses |
# uncertainty to preserve | neighboring seats | relevant standards families
_AUTHORED = r'''
R001|Resolve conflicting system acoustic requirements through a traceable budget and architecture decision|incompatible SPL and battery targets;unowned interface budget|requirement inconsistency rather than transducer deficit;missing usage scenario rather than algorithm defect|allocation margins and unresolved stakeholder constraints|R004 R006|-
R002|Allocate speaker output, excursion and thermal limits across enclosure, amplifier and protection teams|excursion-safe but thermally unsafe drive;enclosure target detached from amplifier rail|power compression rather than insufficient motor force;leakage rather than mistaken EQ|T-S parameter variation and duty-cycle envelope|R009 R016|IEC 60268-5 AES75
R003|Allocate capture sensitivity, self-noise and array spatial budgets across microphone subsystems|adequate single-capsule SNR but aliased array;capsule overload hidden by digital attenuation|capture gain mismatch rather than capsule defect;array spacing rather than NR weakness|capsule spread and talker geometry|R027 R034|IEC 60268-4
R004|Resolve product-level playback/capture interfaces and end-to-end audio latency budgets|individually passing blocks exceed end-to-end delay;echo-reference placement mismatch|transport buffering rather than DSP cost;mechanical coupling rather than AEC tuning|clock drift and subsystem budget covariance|R001 R005|-
R005|Choose bounded DSP architecture consistent with signal bandwidth, delay and stability constraints|filter group delay exceeds interaction budget;enhancement removes desired speech|clipping before DSP rather than filter defect;reference misalignment rather than adaptation failure|finite-window estimates and algorithm operating domain|R024 R044|-
R006|Decide whether verification margins survive measurement uncertainty and reviewer objections|nominal pass with uncertainty crossing limit;shared test oracle masquerading as independent acceptance|fixture bias rather than product failure;insufficient sample size rather than process shift|expanded uncertainty and false acceptance risk|R079 R098|-
R007|Set NPI readiness conditions using capability, yield and reliability evidence|Cp reported without centering;accelerated stress interpreted as field life without model|gage drift rather than process drift;lot mixing rather than supplier deterioration|sampling error and acceleration-model validity|R093 R096|-
R008|Separate source authority, standards applicability and research hypotheses before reuse|bibliography counted as retrieved knowledge;obsolete edition used as current requirement|source duplication rather than corroboration;scope mismatch rather than scientific disagreement|source date, coverage and rights uncertainty|R087 R089|-
R009|Choose sealed/vented speaker alignment against F3, enclosure volume and excursion constraints|tuning below usable excursion range;box leakage spoils predicted alignment|leakage rather than T-S drift;voltage droop rather than acoustic roll-off|small-signal T-S tolerances and enclosure effective volume|R010 R011|IEC 60268-5
R010|Distinguish motor, suspension and inductance mechanisms behind level-dependent impedance and distortion|small-signal parameters reused at large excursion;distortion bins include noise|coil heating rather than Bl nonlinearity;fixture rattling rather than suspension asymmetry|level dependence and parameter-identifiability limits|R009 R016|IEC 60268-5
R011|Size enclosure port and waveguide tradeoffs for tuning, velocity and directivity|end correction omitted;port resonance or chuffing hidden by on-axis FR|turbulence rather than driver THD;boundary loading rather than incorrect port length|effective length, flow regime and boundary conditions|R009 R017|IEC 60268-5 CTA-2034
R012|Choose speaker signal-chain gain and impedance architecture from output noise and headroom budgets|noise references mixed before gain referral;load impedance omitted from stability assessment|ground loop rather than intrinsic op-amp noise;source impedance mismatch rather than codec distortion|noise correlation and gain tolerance|R013 R030|-
R013|Bound amplifier rail, load current and temperature under speaker peak and duty-cycle demands|rail sag clips nominal voltage target;thermal protection threshold lacks duty-cycle margin|power supply droop rather than transducer compression;load phase rather than nominal resistance|supply impedance and transient thermal resistance|R012 R025|-
R014|Verify I2S/TDM transport format, clocking and buffer timing for glitch-free speaker playback|slot-width mismatch;underrun masked by average latency|clock-domain slip rather than DSP overload;format mismatch rather than acoustic fault|jitter, buffer occupancy and worst-case scheduling|R032 R082|-
R015|Design repeatable speaker FR, phase, impedance and distortion measurements with explicit reference conditions|window truncation biases low-frequency FR;voltage reference mistaken for acoustic calibration|time-window artifact rather than resonance;microphone alignment rather than phase defect|distance, gate length, calibration and environmental variation|R016 R033|IEC 60268-5
R016|Derate speaker drive from distortion, compression, temperature and durability limits|low THD interpreted as safe coil temperature;peak power rating applied continuously|thermal compression rather than motor nonlinearity;fixture buzz rather than cone breakup|test duration, duty cycle and failure censoring|R010 R075|AES75 IEC 60268-5
R017|Validate directivity and spatial response across angles rather than a single on-axis trace|sparse angular grid hides lobes;normalization hides absolute off-axis loss|baffle diffraction rather than crossover error;alignment offset rather than asymmetric radiation|angular sampling and microphone position error|R011 R034|CTA-2034
R018|Select tonal EQ from band response and listening-context weighting without hiding narrow resonances|heavy smoothing hides peaks;room cancellation boosted beyond headroom|room notch rather than driver deficit;measurement window rather than tonal imbalance|smoothing bandwidth and spatial averaging|R020 R024|IEC 60268-5
R019|Set bass extension, compression and limiter tradeoffs against excursion and thermal envelopes|bass boost exceeds Xmax;limiter release pumps speech envelope|supply clipping rather than excursion limiting;thermal drift rather than EQ mismatch|crest factor, content spectrum and attack/release transients|R016 R025|AES75
R020|Evaluate perceived speaker balance using level, masking and spectral context|loudness mismatch biases comparison;sharpness proxy presented as listener verdict|level difference rather than preference;room coloration rather than transducer signature|listener population and descriptor validity|R018 R069|-
R021|Select a defensible lumped model and boundary assumptions before escalating to FEM|lumped model used above geometric validity;mesh result claimed from analytic calculation|wrong boundary condition rather than material model;parameter non-identifiability rather than solver issue|model-form error and parameter sensitivity|R009 R022|-
R022|Separate structural vibration and acoustic radiation mechanisms before BEM/vibro-acoustic escalation|structural resonance confused with airborne mode;radiation efficiency assumed constant|mount stiffness rather than panel material;acoustic loading rather than structural damping|coupling strength and unresolved spatial mode shapes|R021 R073|-
R023|Estimate room decay, reflection and system placement limits before ray-based simulation|short IR extrapolated into confident RT60;diffuse-field assumption in small room|noise floor rather than long decay;modal ringing rather than broadband reverberation|decay fit range and spatial nonuniformity|R026 R072|-
R024|Implement speaker EQ and crossover filters with numerical response, delay and clipping checks|unstable or overly resonant coefficients;correct magnitude but incompatible crossover phase|polarity inversion rather than EQ error;finite precision rather than acoustic variation|coefficient precision, sample rate and accumulated headroom|R018 R005|-
R025|Choose smart-amplifier protection thresholds from thermal state, excursion model and sensing delay|resistance drift misread as ambient temperature;feedback latency misses excursion peak|sensor gain error rather than actual heating;model mismatch rather than unsafe content|observer uncertainty, electrical parameter drift and delay|R013 R019|AES75
R026|Decide room-correction limits from spatial response, impulse decay and realizable filter latency|single-position inversion destroys spatial robustness;deep null inversion wastes headroom|position-dependent cancellation rather than loudspeaker defect;late reflection rather than minimum-phase peak|position spread and mixed-phase inversion limits|R023 R071|-
R027|Choose microphone capsule, port and array architecture against sensitivity, noise and overload constraints|port loss ignored in system sensitivity;single-channel target incompatible with array aperture|mesh insertion loss rather than capsule spread;front-end noise rather than acoustic floor|capsule tolerance, pressure reference and acoustic path|R028 R029|IEC 60268-4
R028|Compare MEMS/ECM capsule sensitivity, noise and overload at a common acoustic reference|dBV/Pa confused with dBFS;maximum SPL inferred from small-signal sensitivity|bias network noise rather than capsule noise;calibrator coupling rather than sensitivity shift|calibrator uncertainty and capsule production spread|R027 R030|IEC 60268-4
R029|Choose mic port, mesh and isolation tradeoffs across ingress, wind and acoustic insertion loss|mesh resonance omitted;mechanical rubbing mistaken for wind|structure-borne vibration rather than airflow;blocked vent rather than capsule defect|porosity, leakage path and flow direction|R039 R041|IEC 60268-4
R030|Refer analog microphone noise and headroom through bias, gain and ADC interfaces|input/output noise mixed across gain stages;bias impedance shifts low-frequency response|supply ripple rather than capsule self-noise;common-mode conversion rather than differential signal|noise-source correlation and component tolerance|R012 R031|-
R031|Allocate ADC/PDM clock and quantization noise without confusing bit depth with effective resolution|PDM clock feedthrough aliases in band;digital attenuation hides upstream overload|clock spur rather than acoustic tone;ADC input clipping rather than mic saturation|ENOB assumptions, clock phase noise and decimator response|R030 R032|-
R032|Verify multichannel capture timestamps, channel ordering and buffer continuity|channel swap invalidates array geometry;clock slip creates false TDOA|scheduling gap rather than DOA instability;format packing rather than microphone failure|timestamp granularity and independent clock drift|R014 R043|-
R033|Measure microphone sensitivity, self-noise and overload with explicit pressure and electrical references|dBFS lacks full-scale voltage reference;room noise presented as intrinsic self-noise|calibrator seal leak rather than low sensitivity;preamp noise rather than capsule noise|pressure calibration, noise subtraction and gain uncertainty|R015 R028|IEC 60268-4
R034|Validate microphone-array directionality against angular, gain and delay uncertainty|grating lobes outside sampled angles;calibration mismatch hidden by normalized gain|channel delay bias rather than steering error;spatial aliasing rather than poor estimator|aperture tolerance, phase mismatch and angular sampling|R017 R040|IEC 60268-4
R035|Validate far-field capture under noise, distance and reverberation with realistic speech conditions|stationary-noise success generalized to competing speech;near-field SNR extrapolated to far-field|room decay rather than NR failure;playback leakage rather than ambient noise|talker variability, room variability and nonstationary noise|R038 R041|-
R036|Tune microphone tonal response while preserving intelligibility and overload margin|inverse port boost amplifies self-noise;high-pass corner removes voice fundamentals|mount cavity rather than capsule coloration;distance proximity effect rather than EQ defect|fit position, smoothing and gain headroom|R029 R038|IEC 60268-4
R037|Choose array taper and steering tradeoffs between beamwidth, sidelobes and white-noise gain|narrow beam destroys robustness to mismatch;desired direction overlaps spatial alias|gain mismatch rather than taper choice;wrong geometry rather than bad optimization|sensor phase spread and diffuse-field assumptions|R034 R043|-
R038|Tune speech capture for double-talk, spectral preservation and transient intelligibility|noise metric improves while speech is suppressed;proxy score represented as MOS|level mismatch rather than speech degradation;reference misalignment rather than enhancement damage|speech corpus coverage and perceptual-proxy limits|R035 R044|-
R039|Bound microphone port/mesh resonance and leakage before thermoviscous solver escalation|viscous losses omitted in narrow port;Helmholtz approximation used outside compact geometry|assembly leak rather than mesh impedance;compliance change rather than port length error|effective cavity volume and thermoviscous model-form error|R029 R074|-
R040|Predict array propagation and aliasing with geometric delay and steering-vector checks|far-field plane wave used for near-field source;front/back ambiguity ignored|speed-of-sound drift rather than clock error;channel permutation rather than wave model failure|source range, sound speed and element position|R034 R043|-
R041|Separate wind, room and structure paths in microphone disturbance models|wind spectrum treated as diffuse acoustic noise;vibration integration hides low-frequency drift|mount vibration rather than turbulent pressure;room mode rather than body resonance|flow field, mount transfer path and decay-fit uncertainty|R029 R073|-
R042|Choose echo-control alignment and adaptation constraints across delay and double-talk|echo-return metric computed on misaligned signals;near-end speech removed during adaptation|nonlinear playback rather than insufficient adaptive length;clock drift rather than static delay|echo-path variation and reference timing|R035 R044|-
R043|Estimate TDOA/DOA and beamforming feasibility subject to geometry, aliasing and channel calibration|lag exceeds physically possible aperture delay;front/back ambiguity reported as unique direction|channel reorder rather than source motion;reflection peak rather than direct arrival|sample quantization, aperture error and competing arrivals|R034 R040|-
R044|Choose NR, AGC and dereverb tradeoffs without claiming perceptual quality from a single proxy|AGC masks clipping;denoiser hallucinates or removes speech detail|level normalization rather than true improvement;reference drift rather than dereverb gain|out-of-distribution speech and proxy validity|R038 R042|-
R045|Separate hearing-aid acoustic gain, feedback headroom and output-limit decisions from clinical fitting|coupler response mistaken for real-ear benefit;feedback margin lost at high gain|vent leakage rather than receiver defect;fit change rather than algorithm instability|ear-canal transfer and individual hearing needs|R046 R028|-
R046|Bound OTC/PSAP self-fit acoustic output and usability without inferring medical efficacy|consumer preference promoted to clinical indication;self-fit gain exceeds safe output budget|poor seal rather than insufficient gain;instruction failure rather than algorithm defect|fit variability and user-controlled gain|R045 R049|-
R047|Choose Auracast assistive-listening latency and level budgets across broadcast and receiver paths|multi-receiver desynchronization;broadcast compatibility confused with audibility|transport jitter rather than hearing-device latency;receiver gain rather than content level|receiver diversity and clock synchronization|R081 R083|-
R048|Resolve TWS seal, FF/FB ANC, inward/outward mic and call-capture tradeoffs across user fit|seal leakage invalidates low-frequency ANC;wind or occlusion corrupts voice/feedback mic|tip-fit change rather than driver defect;feedback-path shift rather than feedforward tuning|ear-canal volume, miniature-driver excursion and fit spread|R027 R049|-
R049|Balance circumaural cushion seal, driver output and hybrid ANC stability across head shapes|glasses create low-frequency leak;feedback gain margin collapses with cushion compression|cushion leak rather than insufficient driver bass;mic placement rather than ANC instability|head/cushion fit and feedback-path variation|R048 R019|-
R050|Resolve gaming headset boom pickup, sidetone and duplex latency requirements|sidetone delay distracts speech;boom plosive overload despite quiet-room SNR|mouth-to-boom position rather than capsule defect;USB buffering rather than DSP delay|mouth distance and codec transport latency|R038 R082|-
R051|Choose smartphone earpiece/bottom-speaker and distributed-mic modes under grip and water-mesh constraints|hand blocking changes response;echo reference misses mode-switched playback|grip occlusion rather than manufacturing defect;mesh wetting rather than codec gain|orientation, grip and waterproof membrane variation|R029 R042|-
R052|Allocate tablet edge-speaker and capture performance across portrait, landscape and table placement|case blocks an edge port;table reflection changes beam steering|orientation mapping rather than speaker mismatch;case interference rather than capsule variation|case geometry and tabletop reflection|R051 R053|-
R053|Separate laptop fan, hinge and keyboard-body coupling from speaker/capture processing|fan harmonics contaminate capture;hinge angle changes bezel-array transfer|structure coupling rather than AEC failure;thermal policy rather than microphone defect|fan operating points and hinge angle|R073 R082|-
R054|Resolve monitor/AIO conferencing with bezel array, desk reflection and USB timing|power-supply hum overlaps voice band;display orientation changes desk reflection|ground noise rather than mic self-noise;USB scheduling rather than acoustic delay|desk distance and power configuration|R053 R067|-
R055|Choose smart-speaker far-field array and playback coexistence under room modes and self-echo|woofer playback masks wakeword channels;circular-array aliases on speech harmonics|self-echo nonlinearity rather than NR weakness;room mode rather than transducer peak|placement and far-field talker distribution|R042 R072|-
R056|Resolve soundbar crossover, wall boundary and dialogue/lip-sync tradeoffs|subwoofer polarity cancels crossover;virtual surround optimized at one seat|wall loading rather than woofer defect;transport delay rather than crossover phase|seat variation and soundbar-to-wall distance|R024 R026|CTA-2034
R057|Align multichannel home-theater level, polarity and delay over a listening region|single-seat alignment harms other seats;channel polarity hidden by level normalization|room mode rather than subwoofer delay;miswired channel rather than HRTF rendering|seat-region variation and calibration microphone placement|R026 R071|CTA-2034
R058|Select thin-TV driver and dialogue processing limits under panel buzz and wall placement|panel resonance mistaken for driver breakup;dialogue EQ consumes bass headroom|mount-induced buzz rather than diaphragm fault;wall reflection rather than tonal defect|panel tolerance and placement constraints|R016 R073|IEC 60268-5
R059|Balance doorbell two-way audio against wind, water membrane and feedback paths|wet membrane reduces capture;feedback during close-range intercom|water loading rather than capsule failure;wall mounting rather than echo tuning|wind direction, rain state and mounting surface|R029 R042|-
R060|Allocate appliance voice/notification performance over motor states and duty cycles|motor harmonics mask commands;notification duty cycle overheats small driver|operating-state coupling rather than microphone defect;enclosure leak rather than EQ error|motor load and small-enclosure tolerance|R073 R075|-
R061|Resolve AR open-ear audibility, sound leakage, head tracking and wind capture|privacy leakage grows with level;head movement shifts effective directivity|ear geometry rather than driver mismatch;wind turbulence rather than digital noise|head pose and open-ear fit|R071 R080|-
R062|Bound VR/XR audio motion latency and capture under headset rubbing and occlusion|motion-to-sound delay destabilizes scene;strap rubbing enters microphone|tracking timestamp error rather than renderer delay;mechanical contact rather than ambient noise|pose prediction and physical fit|R071 R080|-
R063|Validate automotive media/hands-free tradeoffs across seats, road noise and cabin echo|driver-seat optimization harms rear passengers;road noise invalidates parked-cabin tuning|seat geometry rather than array defect;vehicle speed rather than NR regression|seat occupancy, speed and cabin state|R035 R042|ITU-T P.1100 ITU-T P.1110
R064|Choose AMR warning and interaction capture budgets around drive noise and moving geometry|warning masked by motors;fixed-source DOA assumption breaks while moving|chassis vibration rather than capsule noise;relative motion rather than clock fault|vehicle speed and motor load|R043 R073|-
R065|Separate quadruped impact and actuator harmonics from field interaction speech|footfall impulses saturate capture;body orientation invalidates fixed beam|mount impact rather than wind;gait mode rather than NR instability|gait phase and microphone isolation|R029 R073|-
R066|Coordinate humanoid self-speech echo, moving joints and conversational directionality|robot speech masks user interruption;joint noise follows head-tracking motion|self-echo path change rather than speech detector error;actuator harmonic rather than human voice|joint state, talker distance and duplex overlap|R042 R043|-
R067|Choose conference array/AEC design for multi-talker double-talk and room decay|dominant-talker steering drops interruptions;AEC tail shorter than room path|clock drift rather than insufficient AEC taps;late reflections rather than array mismatch|room occupancy and talker-position coverage|R042 R035|-
R068|Set directional microphone aperture, steering and calibration limits against alias and ambiguity|narrow beam hides severe sidelobes;unique DOA claimed from symmetric array|channel mismatch rather than steering defect;reflected arrival rather than target movement|aperture spacing and gain/phase calibration|R034 R043|IEC 60268-4
R069|Distinguish measurable psychoacoustic descriptors from listener preference or discomfort|sharpness equated to preference;unmatched loudness biases comparison|level bias rather than spectral preference;test order rather than actual improvement|listener variance and stimulus duration|R020 R070|-
R070|Validate perceptual metric relevance and avoid unsupported MOS predictions|proxy score presented as calibrated MOS;training-language mismatch|reference alignment rather than speech damage;corpus shift rather than algorithm regression|metric confidence and domain coverage|R038 R084|-
R071|Choose binaural/spatial rendering assumptions from HRTF, head pose and temporal alignment|nonindividual HRTF causes front/back reversal;head-tracking delay breaks externalization|pose timestamp error rather than HRTF quality;level cue mismatch rather than ITD|listener anatomy and pose latency|R026 R080|-
R072|Interpret room modes and reverberation without overextending diffuse-field assumptions|RT extrapolated below noise floor;single-position room correction claimed universal|local mode rather than global decay;measurement window rather than absorption change|position distribution and decay-fit interval|R023 R026|-
R073|Identify vibration transfer paths and distinguish structural/acoustic NVH contributions|integration drift dominates displacement;coherence interpreted as causation|mount stiffness rather than source amplitude;electrical pickup rather than mechanical vibration|sensor mounting and transfer-path identifiability|R022 R041|-
R074|Compare mesh/foam/porous acoustic tradeoffs with declared porosity and flow-resistivity assumptions|material model used outside thickness regime;sealing loss attributed to absorption|edge leakage rather than bulk material loss;compression rather than material aging|flow resistivity, compression and boundary layers|R029 R039|-
R075|Bound temperature rise, power compression and reliability duty-cycle tradeoffs|steady thermal model applied to short bursts;room ambient assumed at hot junction|contact resistance rather than coil aging;duty-cycle change rather than material defect|thermal network parameters and censored failure data|R013 R096|-
R076|Separate EMI/ground/clock coupling signatures from acoustic signal-chain noise|hum removed digitally without isolating ground cause;aliased clock spur called acoustic tone|ground loop rather than component self-noise;PDM leakage rather than environmental signal|coupling topology and spectral resolution|R012 R031|-
R077|Evaluate acoustic tolerance and assembly leakage sensitivity across manufacturing distributions|independent tolerances assumed despite correlation;nominal seal used for yield estimate|assembly preload rather than dimensional error;mesh lot rather than cavity size|distribution tails and tolerance covariance|R011 R095|-
R078|Design identifiable DOE and Monte-Carlo analyses with factor interactions and uncertainty|confounded design interpreted causally;Monte-Carlo precision mistaken for model validity|interaction rather than main effect;batch drift rather than treatment effect|sampling design and input distribution validity|R079 R100|-
R079|Build traceable uncertainty and gage R&R budgets with correct references and correlations|repeatability mistaken for total uncertainty;correlated contributors added as independent|fixture bias rather than operator error;drift rather than random spread|coverage factor, covariance and metrological traceability|R006 R078|-
R080|Fuse head/IMU timing with acoustic direction while preserving coordinate-frame uncertainty|frame convention reverses direction;timestamp skew mistaken for motion|sensor alignment rather than DOA error;latency rather than rotational bias|pose covariance and synchronization error|R071 R043|-
R081|Budget Bluetooth/LE Audio transport, buffering and clock constraints without claiming protocol certification|nominal codec frame excludes transport queues;broadcast sync generalized across receivers|packet scheduling rather than codec delay;clock drift rather than jitter burst|radio-condition coverage and receiver implementation|R047 R083|-
R082|Locate OS audio scheduling, resampling and synchronization bottlenecks end to end|average latency hides underrun tails;different clock domains treated as synchronous|scheduler stall rather than DSP overload;resampler drift rather than hardware fault|tail latency and timestamp precision|R014 R032|-
R083|Choose codec/network audio tradeoffs among latency, loss concealment and duplex quality|buffer reduction produces dropouts;packet loss score ignores burst structure|network jitter rather than codec algorithm;reference lag rather than quality loss|loss burst statistics and playout-clock drift|R081 R082|-
R084|Assess local audio ML generalization, leakage and calibration rather than training fit alone|same recording appears in train/test;synthetic accuracy called production robustness|dataset bias rather than feature superiority;label noise rather than model incapacity|held-out domain coverage and prediction uncertainty|R070 R085|-
R085|Preserve acoustic dataset schema, units, provenance and leakage-free partitions|mixed sample-rate channels silently combined;duplicate source recordings leak across splits|unit conversion rather than distribution shift;duplicate capture rather than independent evidence|annotation reliability and missing acquisition metadata|R084 R097|-
R086|Compare products/teardowns under matched conditions and bounded inference|unmatched SPL biases benchmark;teardown appearance promoted to validated topology|firmware mode rather than hardware difference;fixture mismatch rather than product superiority|configuration parity and sampling representativeness|R088 R099|-
R087|Map patent claim elements and prior-art dates with jurisdiction/status and citation provenance|keyword similarity presented as novelty verdict;priority date confused with publication date|claim-scope difference rather than contradiction;family duplicate rather than independent prior art|search coverage, translation and legal interpretation|R088 R089|-
R088|Test acoustic research hypotheses against reproducible sources and discriminating experiments|citation count treated as replication;unavailable raw data hidden by abstract summary|confounding rather than new mechanism;measurement artifact rather than novel effect|replication scope and publication selection bias|R087 R008|-
R089|Determine standards edition, regional applicability and requirement change impact from licensed-access metadata|superseded edition treated as current;informative guidance treated as normative obligation|regional adoption difference rather than conflicting standard;scope exclusion rather than noncompliance|edition status, adoption date and source verification age|R090 R097|-
R090|Build OEM/customer certification traceability without implying ungranted customer approval|customer revision omitted from acceptance matrix;internal pass promoted to certification|customer-specific limit rather than standards conflict;configuration mismatch rather than test failure|customer revision, fixture scope and approval authority|R089 R097|-
R091|Execute deterministic test automation with bounded resource, timeout and evidence contracts|retry hides persistent failure;test process alive mistaken for passed test|fixture state leakage rather than product regression;race condition rather than intermittent hardware|timing determinism and environment provenance|R092 R093|-
R092|Plan safe instrument sequences with verified limits, acquisition provenance and explicit IO authority|dry-run output called physical reading;stimulus exceeds fixture safety limit|driver range mismatch rather than DUT failure;calibration expiry rather than sensitivity drift|instrument range, calibration and synchronization|R091 R079|-
R093|Set factory EOL decision limits from process capability, gage variation and false-reject cost|unguarded limit ignores gage uncertainty;population capability inferred from pilot samples|test fixture drift rather than supplier defect;lot mixture rather than process spread|sampling confidence and gage R&R contribution|R007 R095|-
R094|Rank FACA hypotheses and choose experiments that distinguish root causes before closure|symptom correlation declared root cause;corrective action closed without recurrence test|fixture defect rather than product mechanism;supplier variation rather than design fault|hypothesis coverage and discriminating-test power|R098 R100|-
R095|Separate supplier incoming quality, sampling and traceability from assembly/test-system variation|small sample used to accept shifted lot;certificate treated as measured conformance|incoming lot shift rather than EOL fixture drift;storage exposure rather than supplier process|lot representativeness and sampling acceptance risk|R077 R093|-
R096|Design reliability/HALT stress and censored-life interpretation without inventing lifetime claims|zero failures means infinite life;HALT overstress interpreted as use-condition acceleration|fixture overstress rather than field mechanism;different failure mode rather than same acceleration law|censoring, stress model and confidence bounds|R007 R075|-
R097|Maintain requirement-test-evidence and configuration links across revisions|orphan requirement hidden in denominator;test result linked to wrong hardware/software revision|configuration drift rather than test regression;missing evidence rather than failed requirement|revision ambiguity and incomplete provenance|R089 R099|-
R098|Challenge DFMEA and evidence claims with explicit counterhypotheses and authority boundaries|RPN ranking hides catastrophic severity;consensus presented as independent validation|measurement artifact rather than design mechanism;shared oracle rather than corroboration|failure-mode coverage and reviewer independence limits|R006 R094|-
R099|Curate report claims, evidence hashes and knowledge provenance without domain self-approval|Memory note promoted to Evidence;report conclusion detached from sealed input revision|provenance mismatch rather than conflicting result;stale report rather than changed product|source completeness and unresolved reviewer disagreement|R097 R008|-
R100|Select safe next experiments from informative coverage and observed loss without overriding risk gates|optimizer extrapolates outside safe region;repeated point counted as new information|measurement noise rather than improvement;unexplored interaction rather than poor parameter|surrogate error, exploration coverage and safe bounds|R078 R094|-
'''


STANDARD_FAMILIES=('IEC 60268-5','IEC 60268-4','CTA-2034','AES75','ITU-T P.1100','ITU-T P.1110')
ROLE_DOMAIN_CONTRACTS={
    'R097':{'skill_id':'requirement-association-baseline','method':'methods/roles/requirement-association-baseline.json',
            'suite':'golden/roles/R097/golden.json','scope':'Exact required association/version/reference and supplied interval coverage; no physical/customer acceptance.'},
    'R099':{'skill_id':'requirement-association-domain-review','method':'methods/roles/requirement-association-domain-review.json',
            'suite':'golden/roles/R099/golden.json','scope':'Independent required-association and evidence-content claim challenge; no source authenticity or universal domain authority.'},
    'R094':{'skill_id':'failure-hypothesis-experiment-baseline','method':'methods/roles/failure-hypothesis-experiment-baseline.json',
            'suite':'golden/roles/R094/golden.json','scope':'Supplied failure-model probabilities and controlled experiment selection; not causal proof or recurrence closure.'},
    'R098':{'skill_id':'failure-hypothesis-domain-review','method':'methods/roles/failure-hypothesis-domain-review.json',
            'suite':'golden/roles/R098/golden.json','scope':'Independent FACA model/experiment assertion challenge; no physical root-cause or universal-reviewer authority.'},
    'R043':{'skill_id':'microphone-array-tdoa-baseline','method':'methods/roles/microphone-array-tdoa-baseline.json',
            'suite':'golden/roles/R043/golden.json','scope':'Supplied two-channel GCC-PHAT, peak and direction-cosine ambiguity; not complete beamforming or calibrated DOA.'},
    'R040':{'skill_id':'microphone-array-geometry-domain-review','method':'methods/roles/microphone-array-geometry-domain-review.json',
            'suite':'golden/roles/R040/golden.json','scope':'Independent two-channel signal/geometry/ambiguity review; not unique 3D direction or physical array calibration.'},
    'R015':{'skill_id':'speaker-fr-reference-baseline','method':'methods/roles/speaker-fr-reference-baseline.json',
            'suite':'golden/roles/R015/golden.json','scope':'Supplied sampled FR reference, interval and window validity; not calibrated acquisition or full-band conformance.'},
    'R079':{'skill_id':'speaker-fr-uncertainty-domain-review','method':'methods/roles/speaker-fr-uncertainty-domain-review.json',
            'suite':'golden/roles/R079/golden.json','scope':'Bounded monotone reference-interval review; not full uncertainty metrology or physical qualification.'},
    'R028':{'skill_id':'microphone-reference-domain-review','method':'methods/roles/microphone-reference-domain-review.json',
            'suite':'golden/roles/R028/golden.json','scope':'Bounded pressure/voltage/gain sensitivity review; not physical capsule characterization.'},
    'R030':{'skill_id':'microphone-noise-headroom-domain-review','method':'methods/roles/microphone-noise-headroom-domain-review.json',
            'suite':'golden/roles/R030/golden.json','scope':'Bounded noise identifiability and signal headroom review; not capsule AOP or total peak verification.'},
    'R033':{'skill_id':'microphone-reference-noise-headroom-baseline','method':'methods/roles/microphone-reference-noise-headroom-baseline.json',
            'suite':'golden/roles/R033/golden.json','scope':'Supplied-reference sensitivity, identifiable noise and electrical headroom; not acquired physical measurement.'},
    'R010':{'skill_id':'speaker-nonlinear-domain-review','method':'methods/roles/speaker-nonlinear-domain-review.json',
            'suite':'golden/roles/R010/golden.json','scope':'Bounded RMS distortion and unsupported mechanism attribution review; not whole-role acceptance.'},
    'R075':{'skill_id':'speaker-thermal-domain-review','method':'methods/roles/speaker-thermal-domain-review.json',
            'suite':'golden/roles/R075/golden.json','scope':'Bounded transient thermal and compression counter-hypothesis review; not lifetime verification.'},
    'R005':{'skill_id':'tws-anc-domain-review','method':'methods/roles/tws-anc-domain-review.json',
            'suite':'golden/roles/R005/golden.json','scope':'Bounded FF/FB delay, margin and topology review; not full-loop stability verification.'},
    'R029':{'skill_id':'tws-fit-capture-domain-review','method':'methods/roles/tws-fit-capture-domain-review.json',
            'suite':'golden/roles/R029/golden.json','scope':'Bounded seal and capture noise discrimination review; not physical port/mesh characterization.'},
    'R016':{'skill_id':'speaker-power-distortion-baseline',
            'method':'methods/roles/speaker-power-distortion-baseline.json',
            'suite':'golden/roles/R016/golden.json',
            'scope':'Bounded distortion, power compression and thermal-limit discrimination; not physical reliability qualification.'},
    'R048':{'skill_id':'tws-fit-anc-call-baseline',
            'method':'methods/roles/tws-fit-anc-call-baseline.json',
            'suite':'golden/roles/R048/golden.json',
            'scope':'Bounded TWS seal, FF/FB ANC, outward call noise, excursion and occlusion decisions; not complete product acceptance.'}}


def standards_families(value):
    """Accept complete declared identifiers, never substring approximations."""
    if value=='-': return []
    token='(?:'+'|'.join(re.escape(family) for family in STANDARD_FAMILIES)+')'
    if not re.fullmatch(token+'(?: '+token+')*',value):
        raise ValueError('unknown standards family: '+value)
    parsed=re.findall(token,value)
    if len(parsed)!=len(set(parsed)): raise ValueError('duplicate standards family')
    return [family for family in STANDARD_FAMILIES if family in parsed]


def profiles():
    result={}
    for line in _AUTHORED.strip().splitlines():
        role,decision,failures,counters,uncertainty,neighbors,standards=line.split('|')
        if role in result: raise ValueError('duplicate authored role profile')
        skills=SEAT_SKILLS[int(role[1:])-1].split()
        domain=ROLE_DOMAIN_CONTRACTS.get(role)
        methods=[f'methods/engineering/{s}.json' for s in skills]
        if domain:
            skills.append(domain['skill_id']); methods.append(domain['method'])
        families=standards_families(standards)
        result[role]={'role_id':role,'mission':decision,'professional_decision':decision,
            'common_failure_modes':failures.split(';'),'counter_hypotheses':counters.split(';'),
            'uncertainty_requirements':[uncertainty], 'neighbor_roles':neighbors.split(),
            'standards_metadata_references':families,
            'standards_strategy':'ROLE_SCOPED_METADATA' if families else 'NOT_APPLICABLE_TO_THIS_BOUNDED_METHOD_OR_REQUIRES_TASK_SPECIFIC_RESEARCH',
            'required_skills':skills,
            'required_methods':methods,'domain_execution_contract':copy.deepcopy(domain),
            'professional_decision_contract':{'decision_id':role+'-DOMAIN-DECISION','question':decision,
                'required_methods':methods,
                'required_skills':skills,'acceptance_oracle_source':'SEPARATE_ROLE_DOMAIN_SUITE_REQUIRED'},
            'reviewer_qualifications':{'bounded_domain_question':decision,'must_challenge':counters.split(';'),
                'must_account_for':uncertainty,'human_credential_claimed':False}}
    expected={f'R{i:03d}' for i in range(1,101)}
    if set(result)!=expected: raise ValueError('all 100 explicit professional profiles required')
    for role,profile in result.items():
        if any(n not in result or n==role for n in profile['neighbor_roles']): raise ValueError('invalid neighboring role distinction')
        profile['neighbor_distinctions']=[{'neighbor_role':n,'this_seat_owns':profile['mission'],
                                         'neighbor_owns':result[n]['mission']} for n in profile['neighbor_roles']]
    return result


def enrich_pack(pack):
    """Materialize profession-specific contracts without awarding execution."""
    result=copy.deepcopy(pack); profile=profiles()[pack['identity']['id']]
    for field in ('mission','common_failure_modes','counter_hypotheses','uncertainty_requirements',
                  'standards_metadata_references','standards_strategy','professional_decision_contract','neighbor_distinctions',
                  'required_skills','required_methods'):
        result[field]=copy.deepcopy(profile[field])
    domain=profile['domain_execution_contract']
    if domain:
        result['domain_execution_contract']=copy.deepcopy(domain)
        skill=domain['skill_id']
        result['inputs'][skill]=f'skills/{skill}/input.schema.json'
        result['outputs'][skill]=f'skills/{skill}/output.schema.json'
    result['professional_profile_version']='H0001-authored-v1'
    result['responsibilities']=[profile['mission'],*('Discriminate: '+h for h in profile['counter_hypotheses'])]
    result['scope']=[profile['mission'],*('Investigate and bound: '+f for f in profile['common_failure_modes'])]
    result['non_scope']=['Human clinical, legal, customer or production approval',
        'Physical/calibrated verification without actual instrument and authorized reviewer evidence',
        *('Neighbor '+d['neighbor_role']+' owns: '+d['neighbor_owns'] for d in profile['neighbor_distinctions'])]
    result['professional_inputs']={'decision_question':profile['mission'],
        'required_context':['requirement and numerical limits','product/transducer/lifecycle/risk',
            'input units, provenance and source class',*profile['uncertainty_requirements']],
        'calculation_schemas':copy.deepcopy(result['inputs'])}
    result['professional_outputs']={'decision_id':profile['professional_decision_contract']['decision_id'],
        'required_sections':['bounded engineering disposition','observed failure modes and margins',
            'competing hypotheses and discriminating test','uncertainty and evidence hashes',
            'unresolved domain review and next action'],
        'calculation_schemas':copy.deepcopy(result['outputs'])}
    result['review_requirements']['domain_qualifications']=profile['reviewer_qualifications']
    result['review_requirements']['routing_must_verify_qualification']=True
    result['review_requirements']['legacy_fixed_seat_is_not_domain_acceptance']=True
    for task in result['task_templates']:
        task['professional_objective']=profile['mission']
        task['decision_contract']=profile['professional_decision_contract']['decision_id']
        task['counter_hypotheses']=profile['counter_hypotheses']
    result['report_sections']=[profile['mission'],*profile['common_failure_modes'],
                               *profile['counter_hypotheses'],*profile['uncertainty_requirements']]
    result['current_maturity_level']='L1'
    return result


def professional_report_section(pack):
    return ('\n## Role-specific professional decision\n\n'+pack['mission']+
            '\n\n### Failure mechanisms to distinguish\n\n'+
            '\n'.join('- '+s for s in pack['common_failure_modes'])+
            '\n\n### Competing explanations and discriminating experiments\n\n'+
            '\n'.join('- '+s for s in pack['counter_hypotheses'])+
            '\n\n### Role-specific uncertainty\n\n'+
            '\n'.join('- '+s for s in pack['uncertainty_requirements'])+
            '\n\n### Neighboring role ownership\n\n'+
            '\n'.join('- '+d['neighbor_role']+': '+d['neighbor_owns'] for d in pack['neighbor_distinctions'])+'\n')
