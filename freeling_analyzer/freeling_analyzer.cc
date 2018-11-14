/**
 * Pavel Razgovorov (pr18@alu.ua.es), Universidad de Alicante (https://www.ua.es)
 */
#include <chrono>
#include <codecvt>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include "rapidjson/document.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/stringbuffer.h"

#include "freeling/morfo/analyzer.h"
#include "freeling/output/output_freeling.h"

using namespace std;
using namespace freeling;
using namespace std::filesystem;
using namespace rapidjson;

struct ValueAnalysis {
    string lemmatized_text, lemmatized_text_reduced;

    Value persons, locations, organizations, others,
        numbers, dates;

    ValueAnalysis() {
        lemmatized_text = "";
        lemmatized_text_reduced = "";

        persons = Value(kArrayType);
        locations = Value(kArrayType);
        organizations = Value(kArrayType);
        others = Value(kArrayType);
        numbers = Value(kArrayType);
        dates = Value(kArrayType);
    }
};

inline wstring utf8_to_wstring(const string& str) {
    wstring_convert<codecvt_utf8<wchar_t>> wstring_convert;
    return wstring_convert.from_bytes(str);
}

inline string wstring_to_utf8(const wstring& str) {
    wstring_convert<codecvt_utf8<wchar_t>> wstring_convert;
    return wstring_convert.to_bytes(str);
}

inline bool endsWith(const string& str, const string& suffix) {
    return str.size() >= suffix.size() && 0 == str.compare(str.size() - suffix.size(), suffix.size(), suffix);
}

string& ltrim(string& str, const string& chars = "\t\n\v\f\r ") {
    str.erase(0, str.find_first_not_of(chars));
    return str;
}

string& rtrim(string& str, const string& chars = "\t\n\v\f\r ") {
    str.erase(str.find_last_not_of(chars) + 1);
    return str;
}

string& trim(string& str, const string& chars = "\t\n\v\f\r ") {
    return ltrim(rtrim(str, chars), chars);
}

analyzer::config_options fill_config(const wstring& path) {
    analyzer::config_options cfg;

    /// Language of text to process
    cfg.Lang = L"es";

    // path to language specific data
    wstring lpath = path + cfg.Lang + L"/";

    /// Tokenizer configuration file
    cfg.TOK_TokenizerFile = lpath + L"tokenizer.dat";
    /// Splitter configuration file
    cfg.SPLIT_SplitterFile = lpath + L"splitter.dat";
    /// Morphological analyzer options
    cfg.MACO_Decimal = L".";
    cfg.MACO_Thousand = L",";
    cfg.MACO_LocutionsFile = lpath + L"locucions.dat";
    cfg.MACO_QuantitiesFile = lpath + L"quantities.dat";
    cfg.MACO_AffixFile = lpath + L"afixos.dat";
    cfg.MACO_ProbabilityFile = lpath + L"probabilitats.dat";
    cfg.MACO_DictionaryFile = lpath + L"dicc.src";
    cfg.MACO_NPDataFile = lpath + L"np.dat";
    // cfg.MACO_NPDataFile = lpath + L"nerc/ner/ner-ab-poor1.dat"; // slower
    cfg.MACO_PunctuationFile = path + L"common/punct.dat";
    cfg.MACO_ProbabilityThreshold = 0.001;

    /// NEC config file
    cfg.NEC_NECFile = lpath + L"nerc/nec/nec-ab-poor1.dat";
    /// Sense annotator and WSD config files
    // cfg.SENSE_ConfigFile = lpath + L"senses.dat";
    // cfg.UKB_ConfigFile = lpath + L"ukb.dat";
    /// Tagger options
    cfg.TAGGER_HMMFile = lpath + L"tagger.dat";
    cfg.TAGGER_ForceSelect = RETOK;
    /// Chart parser config file
    // cfg.PARSER_GrammarFile = lpath + L"chunker/grammar-chunk.dat";
    /// Dependency parsers config files
    // cfg.DEP_TxalaFile = lpath + L"dep_txala/dependences.dat";
    // cfg.DEP_TreelerFile = lpath + L"dep_treeler/dependences.dat";
    /// Coreference resolution config file
    // cfg.COREF_CorefFile = lpath + L"coref/relaxcor_constit/relaxcor.dat";

    return cfg;
}

analyzer::invoke_options fill_invoke() {
    analyzer::invoke_options ivk;

    /// Level of analysis in input and output
    ivk.InputLevel = TEXT;
    ivk.OutputLevel = TAGGED;

    /// activate/deactivate morphological analyzer modules
    ivk.MACO_UserMap = false;
    ivk.MACO_AffixAnalysis = true;
    ivk.MACO_MultiwordsDetection = true;
    ivk.MACO_NumbersDetection = true;
    ivk.MACO_PunctuationDetection = true;
    ivk.MACO_DatesDetection = true;
    ivk.MACO_QuantitiesDetection = true;
    ivk.MACO_DictionarySearch = true;
    ivk.MACO_ProbabilityAssignment = true;
    ivk.MACO_CompoundAnalysis = false;
    ivk.MACO_NERecognition = true;
    ivk.MACO_RetokContractions = false;

    ivk.NEC_NEClassification = true;
    ivk.PHON_Phonetics = false;

    // ivk.SENSE_WSD_which = UKB;
    ivk.TAGGER_which = HMM;
    // ivk.DEP_which = TREELER;

    return ivk;
}

void fill_analysis_by_word(ValueAnalysis& va,
                           const string form,
                           const string& lemma,
                           const string& tag,
                           MemoryPoolAllocator<>& alloc) {
    Value val(form.c_str(), alloc);
    switch (tag[0])  /// Determines the word category
    {
        case 'F':    // Punctuation
            return;  // Skip, don't processe it
        case 'A':    /// Adjective
            va.lemmatized_text_reduced += lemma + " ";
            break;
        case 'N':  /// Noun
            va.lemmatized_text_reduced += lemma + " ";
            switch (tag[4])  /// Determines the Named Entity Class (neclass)
            {
                case 'S':  /// Person
                    va.persons.PushBack(val, alloc);
                    break;
                case 'G':  /// Location
                    va.locations.PushBack(val, alloc);
                    break;
                case 'O':  /// Organization
                    va.organizations.PushBack(val, alloc);
                    break;
                case 'V':  /// Other
                    va.others.PushBack(val, alloc);
                    break;
                default:
                    break;
            }
            break;
        case 'V':  /// Verb
            va.lemmatized_text_reduced += lemma + " ";
            break;
        case 'R':  /// Adverb
            if (endsWith(lemma, "mente")) {
                // Only if it ends with "mente" (modal adverb)
                va.lemmatized_text_reduced += lemma + " ";
            }
            break;
        case 'Z':  /// Number
            va.numbers.PushBack(val, alloc);
            break;
        case 'W':  /// Date
            va.dates.PushBack(val, alloc);
            break;
        default:
            break;
    }
    va.lemmatized_text += lemma + " ";
}

ValueAnalysis fill_analysis(const document& doc, MemoryPoolAllocator<>& alloc) {
    ValueAnalysis va;
    for (auto&& paragraph : doc) {
        for (auto&& sentence : paragraph) {
            for (auto&& word : sentence) {
                fill_analysis_by_word(va,
                                      wstring_to_utf8(word.get_form()),
                                      wstring_to_utf8(word.get_lemma()),
                                      wstring_to_utf8(word.get_tag()),
                                      alloc);
            }
        }
    }
    return va;
}

Value analyze_json_value(const document& doc, const wstring& raw_text, MemoryPoolAllocator<>& alloc) {
    ValueAnalysis va = fill_analysis(doc, alloc);
    auto raw_text_utf8 = wstring_to_utf8(raw_text);
    auto raw_text_trimmed = trim(raw_text_utf8);
    auto lemmatized_text_trimmed = trim(va.lemmatized_text);
    auto lemmatized_text_reduced_trimmed = trim(va.lemmatized_text_reduced);
    Value analyzed(kObjectType);
    analyzed.AddMember("raw_text",
                       Value(raw_text_trimmed.c_str(), alloc).Move(), alloc);
    analyzed.AddMember("lemmatized_text",
                       Value(lemmatized_text_trimmed.c_str(), alloc).Move(), alloc);
    analyzed.AddMember("lemmatized_text_reduced",
                       Value(lemmatized_text_reduced_trimmed.c_str(), alloc).Move(), alloc);
    analyzed.AddMember("persons", va.persons, alloc);
    analyzed.AddMember("locations", va.locations, alloc);
    analyzed.AddMember("organizations", va.organizations, alloc);
    analyzed.AddMember("others", va.others, alloc);
    analyzed.AddMember("dates", va.dates, alloc);
    analyzed.AddMember("numbers", va.numbers, alloc);

    return analyzed;
}

void analyze_all_jsons(const analyzer& analyzer) {
    set<string> processed_files;
    fstream processed_files_txt("processed_files.txt", ios_base::in | ios_base::out | ios_base::app);
    processed_files_txt.seekg(ios_base::beg);
    /// Read all processed files
    copy(istream_iterator<string>(processed_files_txt),
         istream_iterator<string>(),
         inserter(processed_files, processed_files.begin()));
    processed_files_txt.seekp(ios_base::end);
    processed_files_txt.clear();  // clear any flags

    const auto dump_path = string(getenv("HOME")) + "/dump";  /// Linux-only
    vector<directory_entry> dirs;
    copy(recursive_directory_iterator(dump_path), recursive_directory_iterator(), back_inserter(dirs));
#pragma omp parallel for
    for (auto iter = dirs.begin(); iter < dirs.end(); ++iter) {
        const auto file_path = (*iter).path().string();
        if (!is_regular_file((*iter).path()) || processed_files.find(file_path) != processed_files.end()) {
            /// Skip dirs and already processed files
            continue;
        }
#pragma omp critical
        cout << "Analyzing " << file_path << endl;

        ifstream json_file(file_path);
        const string json_str((istreambuf_iterator<char>(json_file)),
                              (istreambuf_iterator<char>()));
        json_file.close();
        Document json_doc,
            analyzed_json_doc(kObjectType);
        json_doc.Parse(json_str.c_str());
        auto& alloc = json_doc.GetAllocator();

        /// Copy non-analyzed members
        assert(json_doc.HasMember("date"));
        assert(json_doc.HasMember("province"));
        assert(json_doc.HasMember("url"));
        analyzed_json_doc.AddMember("province", json_doc["province"], alloc);
        analyzed_json_doc.AddMember("date", json_doc["date"], alloc);
        analyzed_json_doc.AddMember("url", json_doc["url"], alloc);

        /// Analyze and copy results
        const char* original_json_members[] = {"title", "lead", "body"};
        for (auto&& member : original_json_members) {
            assert(json_doc.HasMember(member));
            const wstring raw_text = utf8_to_wstring(json_doc[member].GetString());
            /// analyze text, leave result in doc
            document doc;
            analyzer.analyze(raw_text, doc);
            Value analyzed = analyze_json_value(doc, raw_text, alloc);
            analyzed_json_doc.AddMember(StringRef(member), analyzed, alloc);
        }

        /// Write JSON to its origin file
        StringBuffer buffer;
        PrettyWriter<StringBuffer> writer(buffer);
        analyzed_json_doc.Accept(writer);
        const char* output = buffer.GetString();
        ofstream output_json_file(file_path);
        output_json_file << output << endl;
        output_json_file.close();

        /// Write to processed files
#pragma omp critical
        processed_files_txt << file_path << endl;
    }
}

int main(int argc, char** argv) {
    /// set locale to an UTF8 compatible locale
    util::init_locale(L"default");
    /// set config options (which modules to create, with which configuration)
    const auto cfg = fill_config(L"/usr/share/freeling/");
    /// create analyzer
    analyzer analyzer(cfg);

    /// set invoke options (which modules to use)
    const auto ivk = fill_invoke();
    /// load invoke options into analyzer
    analyzer.set_current_invoke_options(ivk);

    /// perform the analysis and measure execution time
    const auto start = chrono::steady_clock::now();
    analyze_all_jsons(analyzer);
    const auto end = chrono::steady_clock::now();
    const auto diff = end - start;
    wcout << L"Time: " << chrono::duration<double, milli>(diff).count() << " ms" << endl;
}
