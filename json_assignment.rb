require 'json'

class ConstructionDetail
  attr_reader :name, :host_element, :adjacent_element, :exposure

  def initialize(name:, host_element:, adjacent_element:, exposure:)
    @name = name
    @host_element = host_element
    @adjacent_element = adjacent_element
    @exposure = exposure
  end

  def match_score(input)
    matches = {}
    total_weight = 0.0
    weighted_score = 0.0

    # Define weights for each attribute
    weights = {
      host_element: 0.4,
      adjacent_element: 0.4,
      exposure: 0.2
    }

    weights.each do |attr, weight|
      total_weight += weight
      detail_value = send(attr)
      input_value = input[attr.to_s]

      if detail_value == input_value
        matches[attr] = :exact
        weighted_score += weight
      elsif fuzzy_match?(detail_value, input_value)
        matches[attr] = :partial
        weighted_score += weight * 0.5
      else
        matches[attr] = :no_match
      end
    end

    {
      score: weighted_score / total_weight,
      matches: matches
    }
  end

  private

  def fuzzy_match?(detail_val, input_val)
    return false if detail_val.nil? || input_val.nil?
    
    detail_lower = detail_val.downcase
    input_lower = input_val.downcase
    
    detail_lower.include?(input_lower) || input_lower.include?(detail_lower)
  end
end

class ContextMatcher
  def initialize
    @details = build_detail_library
  end

  def match(input)
    validate_input!(input)
    
    # Score all details against input
    scored_details = @details.map do |detail|
      result = detail.match_score(input)
      {
        detail: detail,
        score: result[:score],
        matches: result[:matches]
      }
    end

    best_match = scored_details.max_by { |d| d[:score] }

    build_response(best_match, input)
  end

  private

  def build_detail_library
    [
      ConstructionDetail.new(
        name: "External Wall–Slab Junction Waterproofing",
        host_element: "External Wall",
        adjacent_element: "Slab",
        exposure: "External"
      ),
      ConstructionDetail.new(
        name: "Internal Wall–Slab Connection",
        host_element: "Internal Wall",
        adjacent_element: "Slab",
        exposure: "Internal"
      ),
      ConstructionDetail.new(
        name: "External Wall–Roof Flashing Detail",
        host_element: "External Wall",
        adjacent_element: "Roof",
        exposure: "External"
      ),
      ConstructionDetail.new(
        name: "Window–External Wall Head Detail",
        host_element: "External Wall",
        adjacent_element: "Window",
        exposure: "External"
      ),
      ConstructionDetail.new(
        name: "Foundation Wall–Slab Thermal Break",
        host_element: "Foundation Wall",
        adjacent_element: "Slab",
        exposure: "External"
      )
    ]
  end

  def validate_input!(input)
    required_keys = ["host_element", "adjacent_element", "exposure"]
    missing = required_keys - input.keys
    
    raise ArgumentError, "Missing required keys: #{missing.join(', ')}" unless missing.empty?
  end

  def build_response(best_match, input)
    {
      suggested_detail: best_match[:detail].name,
      confidence: best_match[:score].round(2),
      reason: generate_reason(best_match[:matches], input)
    }
  end

  def generate_reason(matches, input)
    exact_matches = matches.select { |_, v| v == :exact }.keys
    partial_matches = matches.select { |_, v| v == :partial }.keys

    if exact_matches.size == 3
      "Exact match on host, adjacent, and exposure"
    elsif exact_matches.size == 2
      matched = exact_matches.map { |k| k.to_s.gsub('_', ' ') }.join(' and ')
      "Exact match on #{matched}"
    elsif exact_matches.size == 1
      "Exact match on #{exact_matches.first.to_s.gsub('_', ' ')}"
    elsif partial_matches.any?
      matched = partial_matches.map { |k| k.to_s.gsub('_', ' ') }.join(', ')
      "Partial match on #{matched}"
    else
      "No strong matches found"
    end
  end
end

matcher = ContextMatcher.new

#testing with different cases. 
input1 = {
  "host_element" => "External Wall",
  "adjacent_element" => "Slab",
  "exposure" => "External"
}

result1 = matcher.match(input1)
puts "Test 1 - Exact Match:"
puts JSON.pretty_generate(result1)
puts "\n" + "="*60 + "\n"

input2 = {
  "host_element" => "External Wall",
  "adjacent_element" => "Roof",
  "exposure" => "Internal"
}

result2 = matcher.match(input2)
puts "Test 2 - Partial Match:"
puts JSON.pretty_generate(result2)
puts "\n" + "="*60 + "\n"

input3 = {
  "host_element" => "Internal Wall",
  "adjacent_element" => "Slab",
  "exposure" => "Internal"
}

result3 = matcher.match(input3)
puts "Test 3 - Different Context:"
puts JSON.pretty_generate(result3)