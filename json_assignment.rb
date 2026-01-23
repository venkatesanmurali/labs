require "json"

class DetailSuggester
  RULES = [
    {
      host_element: "External Wall",
      adjacent_element: "Slab",
      exposure: "External",
      suggested_detail: "External Wall–Slab Junction Waterproofing"
    },
    {
      host_element: "External Wall",
      adjacent_element: "Roof Slab",
      exposure: "External",
      suggested_detail: "External Wall–Roof Slab Upstand Waterproofing"
    },
    {
      host_element: "Basement Wall",
      adjacent_element: "Slab",
      exposure: "Ground",
      suggested_detail: "Basement Wall–Slab Joint Waterbar + Waterproofing"
    }
  ].freeze

  def suggest(input)
    normalized = normalize_input(input)

    best = nil
    best_score = -1
    best_matched = 0

    RULES.each do |rule|
      score, matched = score_rule(rule, normalized)
      next if matched == 0

      if score > best_score
        best = rule
        best_score = score
        best_matched = matched
      end
    end

    build_response(best, best_matched)
  end

  private

  def normalize_input(input)
    {
      host_element: clean(input["host_element"]),
      adjacent_element: clean(input["adjacent_element"]),
      exposure: clean(input["exposure"])
    }
  end

  def clean(val)
    val.to_s.strip
  end

  def score_rule(rule, normalized)
    score = 0
    matched = 0

    # weight exact matches higher
    [:host_element, :adjacent_element, :exposure].each do |key|
      if rule[key] == normalized[key]
        score += 10
        matched += 1
      elsif rule[key].to_s.downcase == normalized[key].to_s.downcase && !normalized[key].empty?
        score += 7
        matched += 1
      elsif !normalized[key].empty? && normalized[key].downcase.include?(rule[key].to_s.downcase)
        score += 4
        matched += 1
      end
    end

    [score, matched]
  end

  def build_response(best_rule, matched_fields)
    if best_rule.nil?
      return {
        "suggested_detail" => nil,
        "confidence" => 0.0,
        "reason" => "No matching rule found"
      }
    end

    confidence =
      case matched_fields
      when 3 then 0.92
      when 2 then 0.75
      when 1 then 0.55
      else 0.0
      end

    reason =
      case matched_fields
      when 3 then "Exact match on host, adjacent, and exposure"
      when 2 then "Partial match on 2 of 3 fields"
      when 1 then "Loose match on 1 field"
      else "No meaningful match"
      end

    {
      "suggested_detail" => best_rule[:suggested_detail],
      "confidence" => confidence,
      "reason" => reason
    }
  end
end

# ---- testing ----
input_json = <<~JSON
{
  "host_element": "External Wall",
  "adjacent_element": "Slab",
  "exposure": "External"
}
JSON

input = JSON.parse(input_json)
output = DetailSuggester.new.suggest(input)

puts JSON.pretty_generate(output)
