# Normalization Range Analysis: [0,1] vs [-1,1]

## Overview

This devplan analyzes whether our model's normalization function should map predicted returns to a [0,1] range or a [-1,1] range. Our current implementation (via the normalization functions in src/v2/predictor.py) transforms predicted returns into scores in the [0,1] range. However, since our model predicts both positive and negative targets, it is worth exploring whether preserving the sign (i.e., using a [-1,1] range) might be more appropriate.

## Current Implementation

- **Normalization Function:**
  - When using the sigmoid or tanh methods, the current implementation maps predictions to a [0,1] range.
  - For example, the tanh method applies the formula `(tanh(k * return_value) + 1) / 2`, which shifts the output from (-1,1) to (0,1).

- **Usage:**
  - The normalized score (in the range [0,1]) is used in the `predict` method to provide a score that, combined with raw predicted returns, determines the rating category (Strong Buy, Buy, Hold, Sell, Strong Sell) via the `get_rating` function.
  - The raw predicted return is directly compared against rating thresholds defined in the configuration.

## Trade-offs

### Using [0,1] Range (Current Approach)

**Pros:**
- **Intuitive for Scoring & UI:** Many systems expect normalized scores within [0,1], making it easier to display and compare values (e.g., as probabilities or percentages).
- **Consistent Thresholds:** The rating system can simply define thresholds like 0.8 for Strong Buy and 0.2 for Strong Sell.
- **Simplified Math:** It avoids dealing with negative scores, which may simplify downstream processing and visualization.

**Cons:**
- **Loss of Sign Information:** Mapping to [0,1] loses the direct representation of the sign of the predicted return. The neutrality point (0 predicted return) becomes 0.5, which might not be immediately intuitive.
- **Indirect Interpretation:** Users must learn that scores above 0.5 indicate positive expectations while those below 0.5 indicate negatives. This extra step might be seen as less direct than using a symmetric scale.

### Using [-1,1] Range

**Pros:**
- **Preserves Sign:** A range of [-1,1] naturally reflects negative and positive predicted returns. Zero remains the neutral midpoint.
- **Direct Interpretation:** Users can directly interpret negative scores as negative predictions and positive scores as positive predictions, which might align better with financial intuition.

**Cons:**
- **Threshold Adjustments:** The rating system (and potentially UI components) might require re-adjustment of thresholds and interpretation. For example, a neutral score would be 0 instead of 0.5.
- **Downstream Impact:** Any component expecting a [0,1] normalized score would have to be reworked, increasing the risk for bugs and inconsistencies.
- **Consistency Issues:** Our current rating mechanism uses raw predicted returns (with thresholds defined in the configuration) and then applies normalization only for display or additional scoring purposes. Changing the range might necessitate changes across the board (including documentation, tests, etc.).

## Recommendation

After careful analysis, the following conclusions are reached:

1. **Preserving Rating Accuracy:** The raw predicted return (used in `get_rating`) is already compared with thresholds that reflect market expectations. The normalized score is used as a complementary measure for scoring and display.

2. **User Interpretation:** A [0,1] range provides a familiar format (like probability percentages). While a [-1,1] range preserves sign, the necessary re-adjustment of thresholds and potential confusion in the UI may not be worth the change.

3. **Potential Hybrid Approach:** One possibility is to expose both normalized values internally, e.g., provide a method to obtain a score in [-1,1] (preserving sign) and another in [0,1] for display. However, this introduces extra complexity which may not be justified unless user feedback clearly indicates a preference.

4. **Backward Compatibility:** Changing from [0,1] to [-1,1] may introduce breaking changes. The current configuration and downstream tasks are set up for [0,1]. Keeping this range maintains consistency.

### Final Decision

It is recommended to **retain the [0,1] normalization range**. The advantages in terms of consistency, ease of integration with UI and downstream processing, and maintaining a standard probability-like scale outweigh the benefits of a symmetric [-1,1] scale. 

The existing configuration can be clearly documented (and exposed via config parameters) to explain that a normalized score of 0.5 represents a neutral prediction. This clarity should resolve ambiguity and help users interpret the results correctly.

## Next Steps

- **Documentation Update:** Clearly document in both the devplan and user-facing docs that normalized scores are in [0,1], along with the interpretation (e.g., 0.5 as neutral, >0.5 as positive, <0.5 as negative).

- **Optional Exposure:** Consider exposing an additional configuration flag if future requirements demand a [-1,1] option. This can be implemented as an alternative normalization method (e.g., 'tanh_signed') that returns results in [-1,1].

- **Testing and Feedback:** Monitor how the normalized scores are used in practice. If users indicate a strong need for a symmetric scale, re-evaluate the trade-offs.

- **Update Configs:** Ensure that all related configuration files and documentation reflect the current decision on normalization range.

## Conclusion

Based on the analysis, the [0,1] range remains the optimal choice for our current system. The normalized score is converted in a manner that is consistent with a probability-like interpretation, while the raw predicted returns (with both positive and negative values) are used for determining ratings. This approach maintains backward compatibility and minimizes disruptions to the existing system. 